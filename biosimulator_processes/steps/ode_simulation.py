import abc

from process_bigraph import Step
from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE


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


class ODEProcess(RunProcess):
    def __init__(self,
                 address: str,
                 model_fp: str,
                 observables: list[list[str]],
                 step_size: float,
                 duration: float,
                 config=None,
                 core=CORE,
                 **kwargs):
        """
            Kwargs:
                'process_address': 'string',
                'process_config': 'tree[any]',
                'observables': 'list[path]',
                'timestep': 'float',
                'runtime': 'float'
        """
        configuration = config or {}
        if not config:
            configuration['process_address'] = address
            configuration['timestep'] = step_size
            configuration['runtime'] = duration
            configuration['process_config'] = {'model': {'model_source': model_fp}}
            configuration['observables'] = observables
        super().__init__(config=configuration, core=core)

    def run(self, inputs=None):
        input_state = inputs or {}
        return self.update(input_state)
