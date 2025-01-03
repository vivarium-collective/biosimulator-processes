import warnings
from basico import *
from process_bigraph import Process
import logging
import os
from pathlib import Path

import cobra
from cobra.io import read_sbml_model
from process_bigraph import Process, Composite
import numpy as np


warnings.filterwarnings("ignore", category=FutureWarning)

logging.getLogger('cobra').setLevel(logging.ERROR)


class ODECopasi(Process):
    """ODE component of the dfba hybrid using COPASI(basico). TODO: Generalize this to use any ode sim."""
    config_schema = {
        'model_file': 'string'
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)
        self.model = load_model(self.config['model_file'])
        self.reaction_names = get_reactions(model=self.model).index.tolist()
        self.species_names = get_species(model=self.model).index.tolist()

    def initial_state(self):
        initial_concentrations = {
            species_name: get_species(species_name, model=self.model).initial_concentration[0]
            for species_name in self.species_names
        }

        initial_derivatives = {
            rxn_id: get_reactions(rxn_id, model=self.model).flux[0]
            for rxn_id in self.reaction_names
        }

        return {
            'species_concentrations': initial_concentrations,
            'reaction_fluxes': initial_derivatives,
            'time': 0.0
        }

    def inputs(self):
        concentrations_type = {
            name: 'float' for name in self.species_names
        }
        return {
            'species_concentrations': concentrations_type,
            'time': 'float'
        }

    def outputs(self):
        concentrations_type = {
            name: 'float' for name in self.species_names
        }

        reaction_fluxes_type = {
            reaction_name: 'float' for reaction_name in self.reaction_names
        }

        return {
            'species_concentrations': concentrations_type,
            'reaction_fluxes': reaction_fluxes_type,
            'time': 'float'
        }

    def update(self, inputs, interval):
        for cat_id, value in inputs['species_concentrations'].items():
            set_type = 'concentration'
            species_config = {
                'name': cat_id,
                'model': self.model,
                set_type: value
            }
            set_species(**species_config)

        # run model for "interval" length; we only want the state at the end
        tc = run_time_course(
            start_time=inputs['time'],
            duration=interval,
            update_model=True,
            model=self.model
        )

        results = {'time': interval}
        results['species_concentrations'] = {
            mol_id: float(get_species(
                name=mol_id,
                exact=True,
                model=self.model
            ).concentration[0])
            for mol_id in self.species_names
        }

        results['reaction_fluxes'] = {
            rxn_id: float(get_reactions(
                name=rxn_id,
                model=self.model
            ).flux[0])
            for rxn_id in self.reaction_names
        }

        return results


class FBA(Process):
    """FBA component of the dfba hybrid using COBRA."""
    config_schema = {
        'model_file': 'string',
        'objective': {
            'domain': 'string',  # either protein or mrna
            'name': 'string',  # specific to the model: i.e., LacI
            'scaling_factor': 'float'
        }
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        # create model
        model_file = self.config['model_file']
        data_dir = Path(os.path.dirname(model_file))
        path = data_dir / model_file.split('/')[-1]
        self.model = read_sbml_model(str(path.resolve()))

        # parse objective
        self.objective_domain = self.config['objective']['domain']
        self.objective_name = self.config['objective']['name']
        self.scaling_factor = self.config['objective'].get('scaling_factor', 10)

        # set objectives
        self.model.objective = {
            self.model.reactions.get_by_id(reaction.id): np.random.random()  # TODO: make this more realistic
            for reaction in self.model.reactions
        }

        # set even bounds
        for reaction in self.model.reactions:
            rand_bound = np.random.random()
            self.model.reactions.get_by_id(reaction.id).lower_bound = -rand_bound  # TODO: What to do here?
            self.model.reactions.get_by_id(reaction.id).upper_bound = rand_bound

    def initial_state(self):
        initial_fluxes = {}
        initial_solution = self.model.optimize()
        if initial_solution.status == 'optimal':
            initial_fluxes = {
                reaction.name: reaction.flux
                for reaction in self.model.reactions
            }

        return {'fluxes': initial_fluxes}

    def inputs(self):
        return {'reaction_fluxes': 'tree[float]'}

    def outputs(self):
        return {'fluxes': 'tree[float]'}

    def update(self, state, interval):
        for reaction_name, reaction_flux in state['reaction_fluxes'].items():
            for reaction in self.model.reactions:
                if reaction.name == reaction_name:
                    # 1. reset objective weights according to reaction fluxes directly
                    self.model.objective = {
                        self.model.reactions.get_by_id(reaction.id): reaction_flux
                    }

                    # 2. set lower bound with scaling factor and reaction fluxes
                    self.model.reactions.get_by_id(reaction.id).lower_bound = -self.scaling_factor * abs(reaction_flux)  # / (5 + abs(reaction_flux))

        # 3. solve for fluxes
        output_state = {}
        solution = self.model.optimize()
        if solution.status == "optimal":
            data = dict(zip(
                list(state['reaction_fluxes'].keys()),
                list(solution.fluxes.to_dict().values())
            ))
            output_state['fluxes'] = data

            # TODO: do we want to instead scale by input flux?
            # for reaction in self.model.reactions:
            #     flux = solution.fluxes[reaction.id]
            #     for reaction_name, reaction_flux in state['reaction_fluxes'].items():
            #         if reaction.name == reaction_name:
            #             fluxes[reaction.name] = flux * reaction_flux

        return output_state
