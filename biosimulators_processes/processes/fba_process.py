import logging
import os
from pathlib import Path

import cobra
from cobra.io import load_model as load_cobra, read_sbml_model
from process_bigraph import Process, Composite
import numpy as np

from biosimulators_processes import CORE


logging.getLogger('cobra').setLevel(logging.ERROR)


class Cobra(Process):
    config_schema = {
        'model_file': 'string',
        'objective': {
            'domain': 'string',  # either protein or mrna
            'name': 'string',  # specific to the model: i.e., LacI
            'scaling_factor': 'float'
        }
    }

    def __init__(self, config=None, core=CORE):
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
        initial_solution = self.model.optimize()
        initial_fluxes = {}
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
                    self.model.reactions.get_by_id(reaction.id).lower_bound = -self.scaling_factor * abs(reaction_flux)

        # 3. solve for fluxes
        fluxes = {}
        solution = self.model.optimize()
        if solution.status == "optimal":
            fluxes = dict(zip(
                list(state['reaction_fluxes'].keys()),
                list(solution.fluxes.to_dict().values())
            ))

            # TODO: do we want to instead scale by input flux?
            # for reaction in self.model.reactions:
            #     flux = solution.fluxes[reaction.id]
            #     for reaction_name, reaction_flux in state['reaction_fluxes'].items():
            #         if reaction.name == reaction_name:
            #             fluxes[reaction.name] = flux * reaction_flux

        return fluxes
