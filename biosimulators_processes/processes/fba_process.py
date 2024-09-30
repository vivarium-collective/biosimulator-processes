import cobra
from cobra.io import load_model as load_cobra, read_sbml_model
from process_bigraph import Process, Composite
from biosimulators_processes import CORE


class Cobra(Process):
    config_schema = {
        'model_file': 'string'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.model = read_sbml_model(config['model_file'])

    def inputs(self):
        return {'reaction_derivatives': 'tree[float]'}

    def outputs(self):
        return {'fluxes': 'tree[float]'}

    def update(self, state, interval):
        # set lower bound
        for reaction_id, reaction_derivative in state['reaction_derivatives'].items():
            for reaction in self.model.reactions:
                if reaction.name == reaction_id:
                    self.model.reactions.get_by_id(reaction.id).lower_bound = -reaction_derivative

        # run solver
        fluxes = {}
        solution = self.model.optimize()
        if solution.status == "optimal":
            for reaction in self.model.reactions:
                rxn_flux = solution.fluxes[reaction.id]
                fluxes[reaction.name] = rxn_flux

        return fluxes


