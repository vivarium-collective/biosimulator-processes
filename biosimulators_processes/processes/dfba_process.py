import os
import warnings
from pathlib import Path
from types import FunctionType
from typing import *

import numpy as np
import cobra
from cobra.io import read_sbml_model
from basico import *
from process_bigraph import Process, Composite, ProcessTypes
from scipy.integrate import solve_ivp

from biosimulators_processes import CORE
from biosimulators_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulators_processes.simulator_functions import SIMULATOR_FUNCTIONS


class DynamicFBA(Process):
    config_schema = {
        'model': MODEL_TYPE,
        'simulator': {  # TODO: expand this
            '_type': 'string',
            '_default': 'copasi'
        },
        'start': 'integer',
        'stop': 'integer',
        'steps': 'integer'
    }

    def __init__(self, config, core):
        super().__init__(config, core)
        model_file = self.config['model']['model_source']
        self.simulator = self.config['simulator']

        # create cobra model
        data_dir = Path(os.path.dirname(model_file))
        path = data_dir / model_file.split('/')[-1]
        self.fba_model = read_sbml_model(str(path.resolve()))

        # create utc model (copasi)
        self.utc_model = load_model(model_file)

        # set time params
        self.start = self.config['start']
        self.stop = self.config['stop']
        self.steps = self.config['steps']

    def initial_state(self):
        # 1. get initial species concentrations from simulator
        # 2. influence fba bounds with #1
        # 3. call cobra_model.optimize() and give vals
        pass

    def inputs(self):
        pass

    def outputs(self):
        return {'solution': 'tree[float]'}

    def update(self, state, interval):
        # get state TODO: move this to initial_state()
        spec_data = get_species(model=self.utc_model)
        species_output_names = spec_data.index.tolist()
        reactions = self.fba_model.reactions
        reaction_mappings = self._generate_reaction_mappings(species_output_names, reactions)
        initial_concentrations = list(spec_data.initial_concentration.to_dict().values())

        # run dfba and get solution
        solution = self._run_dfba_simulation(species_output_names, initial_concentrations, reaction_mappings)
        return {'solution': solution}

    def _set_dynamic_bounds(self, model, concentration_dict, mappings):
        """
        Update reaction bounds dynamically based on species concentrations.

        Parameters:
            model: The COPASI model object
            concentration_dict: Dictionary of species concentrations (floating concentrations)
            mappings: List of reaction mappings (from species to reactions)
        """
        for species, concentration in concentration_dict.items():
            for mapping in mappings:
                if species in mapping:
                    reaction_name = mapping[species]
                    # TODO: adjust lower bound based on concentration (you can modify logic as needed)
                    max_import = -10 * concentration / (5 + concentration)
                    set_reaction_parameters(
                        name='lower_bound',
                        value=max_import,
                        reaction_name=reaction_name,
                        model=model
                    )

    def _dynamic_system(self, t, y, species_names, mappings):
        """
        Calculate time derivatives of species using a dynamic system.

        Parameters:
            t: Current time
            y: Array of species concentrations
            mappings: List of mappings (species to reactions)

        Returns:
            Fluxes calculated based on current concentrations
        """
        # Convert the concentrations array (y) into a dictionary for easier handling
        concentration_dict = dict(zip(species_names, y))

        # Dynamically update reaction bounds based on the current concentrations
        self._set_dynamic_bounds(self.utc_model, concentration_dict, mappings)

        # Run the time course for a single time step (you can adjust the logic here)
        results = run_time_course(
            model=self.utc_model,
            start=t,
            end=t + 0.1,  # Small time step
            steps=1,
            update_model=True
        )

        # Extract fluxes from the simulation results
        fluxes = []
        for species in species_names:
            flux = results[species].values[-1]  # Extract the last value for the species
            fluxes.append(flux)

        return fluxes

    def _run_dfba_simulation(self, species_names, initial_concentrations, mappings):
        """
        Run the dynamic FBA (dFBA) simulation using the dynamic system and solve_ivp.

        Parameters:
            species_names: Names of species to simulate
            initial_concentrations: Initial concentrations for the species
            mappings: List of mappings (species to reactions)
        """
        time_points = np.linspace(self.start, self.stop, self.steps)  # From 0 to 15, with 100 time points
        sol = solve_ivp(
            fun=lambda t, y: self._dynamic_system(t, y, species_names, mappings),
            t_span=(self.start, self.stop),
            y0=initial_concentrations,
            t_eval=time_points,
            method='BDF',  # stiff solver TODO: Change this dynamically (check for it)
            rtol=1e-6,
            atol=1e-8
        )

        return sol

    def _generate_reaction_mappings(self, output_names, reactions) -> list[dict]:
        mappings = []
        for reaction in reactions:
            for name in output_names:
                rxn = [r.lower() for r in list(reaction.values()).split(" ")]
                obs_name = name.split(" ")[0].lower()
                obs_type = name.split(" ")[-1]
                if obs_name in rxn:
                    mapping = {}
                    if "transcription" in rxn and obs_type == "mRNA":
                        mapping = {name: reaction.name}
                    elif "translation" in rxn and obs_type == "protein":
                        mapping = {name: reaction.name}
                    elif "degradation" in rxn:
                        if "transcripts" in rxn and obs_type == "mRNA":
                            mapping = {name: reaction.name}
                        elif "transcripts" not in rxn and obs_type == "protein":
                            mapping = {name: reaction.name}
                    if mapping:
                        mappings.append(mapping)
        return mappings


