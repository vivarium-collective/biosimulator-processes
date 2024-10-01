import logging

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
            'name': 'string'  # specific to the model: i.e., LacI
        }
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.model = read_sbml_model(self.config['model_file'])

        # parse objective
        objective_domain = self.config['objective']['domain']
        objective_name = self.config['objective']['name']
        for reaction in self.model.reactions:
            rxn_name = reaction.name
            if objective_domain in rxn_name and objective_name in rxn_name:
                self.model.objective = reaction.id

    def initial_state(self):
        # set random lower bound for initial state TODO: make this more accurate/dynamic
        for reaction in self.model.reactions:
            sampled_lb = np.random.random()
            self.model.reactions.get_by_id(reaction.id).lower_bound = -sampled_lb

        # solve initially
        initial_solution = self.model.optimize()
        initial_fluxes = {
            reaction.name: initial_solution.fluxes[reaction.id]
            for reaction in self.model.reactions
        }

        return {'fluxes': initial_fluxes}

    def inputs(self):
        return {'reaction_derivatives': 'tree[float]'}

    def outputs(self):
        return {'fluxes': 'tree[float]'}

    def update(self, state, interval):
        # add objectives
        for reaction in self.model.reactions:
            self.model.objective = reaction.id

        # set lower bound
        for reaction_name, reaction_derivative in state['reaction_derivatives'].items():
            for reaction in self.model.reactions:
                if reaction.name == reaction_name:
                    self.model.reactions.get_by_id(reaction.id).lower_bound = -reaction_derivative

        # run solver
        fluxes = {}
        solution = self.model.optimize()
        if solution.status == "optimal":
            for reaction in self.model.reactions:
                rxn_flux = solution.fluxes[reaction.id]
                fluxes[reaction.name] = rxn_flux

        return fluxes


