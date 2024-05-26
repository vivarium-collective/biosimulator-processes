import abc

from process_bigraph import Step
from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE
from biosimulator_processes.utils import calc_num_steps, calc_duration, calc_step_size


class OdeSimulation(Step, abc.ABC):
    config_schema = {
        'sbml_filepath': 'string',
        'time_config': {
            'step_size': 'maybe[float]',
            'num_steps': 'maybe[float]',
            'duration': 'maybe[float]'
        }
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        assert len(list(self.config['time_config'].values())) >= 2, "you must pass two of either: step size, n steps, or duration."
        self.step_size = self.config.get('step_size')
        self.num_steps = self.config.get('num_steps')
        self.duration = self.config.get('duration')
        self._set_time_params()

    def _set_time_params(self):
        if self.step_size and self.num_steps:
            self.duration = calc_duration(self.num_steps, self.step_size)
        elif self.step_size and self.duration:
            self.num_steps = calc_num_steps(self.duration, self.step_size)
        else:
            self.step_size = calc_step_size(self.duration, self.num_steps)

    @abc.abstractmethod
    def _set_simulator(self, sbml_fp: str) -> object:
        """Load simulator instance"""
        pass

    @abc.abstractmethod
    def _get_floating_species_ids(self) -> list[str]:
        """Sim specific method"""
        pass

    '''@abc.abstractmethod
    def _set_floating_species(self):
        """Sim specific method for starting values relative to this property."""
        pass

    @abc.abstractmethod
    def _set_global_parameters(self):
        """Sim specific method for starting values relative to this property."""
        pass

    @abc.abstractmethod
    def _set_reactions(self):
        """Sim specific method for starting values relative to this property."""
        pass'''

    def inputs(self):
        """For now, none"""
        return {}

    def outputs(self):
        return {
            'time': 'float',
            'floating_species': {
                spec_id: 'float'
                for spec_id in self.floating_species_ids
            }
        }

    @abc.abstractmethod
    def update(self, inputs):
        """Iteratively update over self.floating_species_ids as per the requirements of the simulator library."""
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
