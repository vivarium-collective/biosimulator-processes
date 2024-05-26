import abc
from process_bigraph import Step


class OdeSimulation(Step, abc.ABC):
    config_schema = {
        'sbml_filepath': 'string',
        'n_steps': 'integer',
        'step_size': 'float',
        'duration': {
            '_type': 'string',
            '_default': 10}
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

    @abc.abstractmethod
    def inputs(self):
        pass

    @abc.abstractmethod
    def outputs(self):
        pass

    def update(self, inputs):
        pass

    @abc.abstractmethod
    def set_species_list(self):
        pass

    @abc.abstractmethod
    def set_global_parameters(self):
        pass

    @abc.abstractmethod
    def set_reactions(self):
        pass
