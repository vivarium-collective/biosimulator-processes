import os
import warnings
from pathlib import Path

from scipy.integrate import solve_ivp
import matplotlib.pyplot as plt
import cobra
from cobra.io import load_model as load_cobra, read_sbml_model
from basico import * 
import numpy as np
from tqdm import tqdm
from process_bigraph import Process

from biosimulators_processes.helpers import generate_reaction_mappings
from biosimulators_processes import CORE
from biosimulators_processes.data_model.sed_data_model import MODEL_TYPE


# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning, module="cobra.util.solver")
warnings.filterwarnings("ignore", category=FutureWarning, module="cobra.medium.boundary_types")

# TODO -- can set lower and upper bounds by config instead of hardcoding
MODEL_FOR_TESTING = load_cobra('textbook')


# TODO: possibly take in input state of copasi concentrations instead of hardcoded current implementation

class DynamicFBA(Process):
    """
    Performs dynamic FBA.

    Parameters:
    - model: The metabolic model for the simulation.
    - kinetic_params: Kinetic parameters (Km and Vmax) for each substrate.
    - biomass_reaction: The identifier for the biomass reaction in the model.
    - substrate_update_reactions: A dictionary mapping substrates to their update reactions.
    - biomass_identifier: The identifier for biomass in the current state.

    TODO -- check units
    """

    config_schema = {
        'model_file': 'string',
        'model': 'Any',
        'kinetic_params': 'map[tuple[float,float]]',
        'biomass_reaction': {
            '_type': 'string',
            '_default': 'Biomass_Ecoli_core'
        },
        'substrate_update_reactions': 'map[string]',
        'biomass_identifier': 'string',
        'bounds': 'map[bounds]',
    }

    def __init__(self, config, core):
        super().__init__(config, core)

        if self.config['model_file'] == 'TESTING':
            self.model = MODEL_FOR_TESTING
        elif not 'xml' in self.config['model_file']:
            # use the textbook model if no model file is provided
            self.model = load_model(self.config['model_file'])
        elif isinstance(self.config['model_file'], str):
            self.model = cobra.io.read_sbml_model(self.config['model_file'])
        else:
            # error handling
            raise ValueError('Invalid model file')

        for reaction_id, bounds in self.config['bounds'].items():
            if bounds['lower'] is not None:
                self.model.reactions.get_by_id(reaction_id).lower_bound = bounds['lower']
            if bounds['upper'] is not None:
                self.model.reactions.get_by_id(reaction_id).upper_bound = bounds['upper']

    def inputs(self):
        return {
            'substrates': 'map[positive_float]'
        }

    def outputs(self):
        return {
            'substrates': 'map[positive_float]'
        }

    # TODO -- can we just put the inputs/outputs directly in the function?
    def update(self, state, interval):
        substrates_input = state['substrates']

        for substrate, reaction_id in self.config['substrate_update_reactions'].items():
            Km, Vmax = self.config['kinetic_params'][substrate]
            substrate_concentration = substrates_input[substrate]
            uptake_rate = Vmax * substrate_concentration / (Km + substrate_concentration)
            self.model.reactions.get_by_id(reaction_id).lower_bound = -uptake_rate

        substrate_update = {}

        solution = self.model.optimize()
        if solution.status == 'optimal':
            current_biomass = substrates_input[self.config['biomass_identifier']]
            biomass_growth_rate = solution.fluxes[self.config['biomass_reaction']]
            substrate_update[self.config['biomass_identifier']] = biomass_growth_rate * current_biomass * interval

            for substrate, reaction_id in self.config['substrate_update_reactions'].items():
                flux = solution.fluxes[reaction_id] * current_biomass * interval
                old_concentration = substrates_input[substrate]
                new_concentration = max(old_concentration + flux, 0)  # keep above 0
                substrate_update[substrate] = new_concentration - old_concentration
                # TODO -- assert not negative?
        else:
            # Handle non-optimal solutions if necessary
            # print('Non-optimal solution, skipping update')
            for substrate, reaction_id in self.config['substrate_update_reactions'].items():
                substrate_update[substrate] = 0

        return {
            'substrates': substrate_update,
        }


def add_dynamic_bounds(*args):
    """
    # 1. get reaction mappings 
    # 2. y = get_species(model=copasi).initial_concentration.values
    # 3. for each species in y, calculate max import (TODO: make this specific)
    # 4. for each species mapping, use the dict val (reaction name) to say fba_model.reactions.get_by_id(reaction_name) = max_import
    """
    # Zip species names and their corresponding concentrations for iteration
    fba_model = args[0]
    y = args[1]
    mappings = args[2]
    species_concentrations = y  # dict(zip(species_names, y))
    for mapping in mappings:
        for species, reaction_name in mapping.items():  # Each mapping is a dictionary like {'LacI mRNA': 'degradation of LacI transcripts'}
            if species in species_concentrations:
                concentration = species_concentrations[species]
                rxn_id = reaction_name.replace(" ", "_")
                for reaction in fba_model.reactions:
                    # TODO: make this more specific
                    if "degradation" in reaction_name:
                        max_import = -10 * concentration / (5 + concentration)
                        fba_model.reactions.get_by_id(reaction.id).lower_bound = max_import
                    elif "transcription" in reaction_name:
                        max_import = 5 * concentration / (3 + concentration)
                        fba_model.reactions.get_by_id(reaction.id).lower_bound = max_import
                    elif "translation" in reaction_name:
                        max_import = 8 * concentration / (4 + concentration)
                        fba_model.reactions.get_by_id(reaction.id).lower_bound = max_import


def apply_mm_kinetics(concentration, Vmax, Km):
    """Apply Michaelis-Menten kinetics to calculate the flux."""
    return (Vmax * concentration) / (Km + concentration)


n_dynamic_system_calls = 0

def dynamic_system(t, y, fba_model, utc_model, mappings):
    # The issue with less time point data vs appropriate scale specified will be solvved with pbg if we simply connect to the copasi process output ports as inputs 
    # reference global store TODO: this will be state arg within the Pbg update method
    global n_dynamic_system_calls
    n_dynamic_system_calls += 1
    global input_state 
    # calc duration TODO: again this will be done by pbg
    t_prev = input_state['time'][-1]
    # run copasi for teh given dur
    run_time_course(t_prev, t, 1, model=utc_model, update_model=True, use_numbers=True)
    # output_names = get_species(model=copasi).index.tolist()
    # run_time_course_with_output(output_selection=output_names, intervals=1, model=copasi, update_model=True, use_numbers=True)
    # track times TODO: this will be done by pbg as output AND input ports
    input_state['time'].append(t)
    # set y to this value array
    y = get_species(model=utc_model)['concentration'].to_dict()
    # update global store TODO: do this with process bigraph
    for name, value in y.items():
        input_state['floating_species_concentrations'][name].append(value)
        concentrations[name].append(value)
    # update the FBA model's reaction bounds using species concentrations and mappings
    add_dynamic_bounds(fba_model, utc_model, y, mappings)
    # Run FBA with updated bounds and calculate fluxes, first clearing constraints
    # cobra.util.add_lp_feasibility(fba_model)
    fba_model = add_lp_feasibility_with_check(fba_model)
    feasibility = cobra.util.fix_objective_as_constraint(fba_model)
    # Example of reactions to optimize (can vary based on your specific model)
    reaction_list = [rxn.id for rxn in fba_model.reactions]
    obj_directions = ['max' for _ in reaction_list]  # TODO: make this more fine-grained
    lex_constraints = cobra.util.add_lexicographic_constraints(fba_model, reaction_list, obj_directions)
    # scale fluxes by the concentration for each species at time t: either for biomass or by mm kinetics
    fluxes = []
    for species, concentration in y.items():
        if species in concentrations.keys():
            # handle scaling by biomass
            if species == 'biomass':
                biomass_concentration = y['biomass']
                flux = lex_constraints.values * biomass_concentration
                fluxes.append(flux)
            else:
                # handle scaling by mm kinetics TODO: change this to be dynamic input
                Vmax, Km = 10, 5
                flux = apply_mm_kinetics(concentration, Vmax, Km)
                fluxes.append(flux)
        else:
            # give raw values if not TODO: handle this differently
            fluxes.append(lex_constraints.values)
    # update progress bar
    if dynamic_system.pbar is not None:
        dynamic_system.pbar.update(1)
        dynamic_system.pbar.set_description(f't = {t:.3f}')
    return fluxes


dynamic_system.pbar = None


def infeasible_event(t, y, fba_model, utc_model, mappings):
    """
    Determine solution feasibility.

    Avoiding infeasible solutions is handled by solve_ivp's built-in event detection.
    This function re-solves the LP to determine whether or not the solution is feasible
    (and if not, how far it is from feasibility). When the sign of this function changes
    from -epsilon to positive, we know the solution is no longer feasible.

    """
    with fba_model:
        add_dynamic_bounds(fba_model, utc_model, y, mappings)
        # cobra.util.add_lp_feasibility(fba_model)
        updated_model = add_lp_feasibility_with_check(fba_model)
        feasibility = cobra.util.fix_objective_as_constraint(updated_model)
        # feasibility = fba_model.optimize().objective_value 

    val = feasibility - infeasible_event.epsilon
    return val


def add_lp_feasibility_with_check(fba_model):
    """Add LP feasibility constraints with a check for existing constraints."""
    prob = fba_model.problem  # Access the solver

    for met in fba_model.metabolites:
        # Check if the feasibility variables already exist and remove them
        s_plus_name = "s_plus_" + met.id
        s_minus_name = "s_minus_" + met.id
        
        if s_plus_name in fba_model.variables:
            fba_model.remove_cons_vars(fba_model.variables[s_plus_name])
        if s_minus_name in fba_model.variables:
            fba_model.remove_cons_vars(fba_model.variables[s_minus_name])
        
        # Now add the new variables
        s_plus = prob.Variable(s_plus_name, lb=0)
        s_minus = prob.Variable(s_minus_name, lb=0)
        
        fba_model.add_cons_vars([s_plus, s_minus])

        # Add constraint if missing
        if met.id not in fba_model.constraints:
            fba_model.constraints[met.id] = prob.Constraint(0, name=met.id)
        
        # Set the linear coefficients
        fba_model.constraints[met.id].set_linear_coefficients({s_plus: 1.0, s_minus: -1.0})

    return fba_model


def run_dfba():
    # time params TODO: make these config params
    start = 400
    stop = 1000
    steps = 600
    ts = np.linspace(start, stop, steps + 1)

    # initial state
    global concentrations
    global input_state 
    initial_concentrations = get_species(model=copasi)['initial_concentration'].to_dict()
    concentrations = {name: [initial_concentrations[name]] for name in initial_concentrations.keys()}
    input_state = {
        'floating_species_concentrations': {name: [initial_concentrations[name]] for name in initial_concentrations.keys()},
        'time': [start],
    }
    y0 = list(initial_concentrations.values())
    mappings = generate_reaction_mappings(list(initial_concentrations.keys()), cobrapy)
    # add_dynamic_bounds(cobrapy, copasi, initial_concentrations, mappings)

    # solver params
    method = 'BDF'  # 'BDF', 'RK45'
    rTol = 1e-5
    aTol = 1e-7
    infeasible_epsilon = 1e-6
    infeasible_direction = 1 

    # set infeasibility params TODO: make this config params
    infeasible_event.epsilon = infeasible_epsilon
    infeasible_event.direction = infeasible_direction
    infeasible_event.terminal = True
    # run and get solution
    with tqdm() as pbar:
        dynamic_system.pbar = pbar

        sol = solve_ivp(
            fun=dynamic_system,
            events=[infeasible_event],
            t_span=(ts.min(), ts.max()),
            y0=y0,
            t_eval=ts,
            rtol=rTol,
            atol=aTol,
            method=method,
            args=(cobrapy, copasi, mappings)
        )
    state = input_state.copy()
    state.update({'fluxes': sol.y.tolist()})
    # remove extra timepoints TODO: pbg will take care of this 
    for key, val in state.items():
        if isinstance(val, list):
            if key == "time":
                state[key] = sol.t.tolist()
        else:
            for name, datum in val.items():
                state[key][name] = list(set(datum))
    return state 