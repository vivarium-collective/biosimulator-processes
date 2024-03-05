from typing import *
from abc import abstractmethod
from process_bigraph import Step
from biosimulator_processes.data_model import TimeCourseProcessConfigSchema
from biosimulator_processes.processes.copasi_process import CopasiProcess


class ParameterScan(Step):
    config_schema = {
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]',  # ie: 'param_type: param_name'... like 'global': 'ADP', 'species': 'S3'
        'process_config': 'tree[string]'}  # use the builder to extract this

    @abstractmethod
    def inputs(self):
        pass

    @abstractmethod
    def outputs(self):
        pass

    @abstractmethod
    def initial_state(self):
        pass

    @abstractmethod
    def update(self, state):
        pass


class DeterministicTimeCourseParameterScan(ParameterScan):
    """Using CopasiProcess as the primary TimeCourse simulator.

        # TODO: enable multiple Simulator types.
    """
    config_schema = {
        'process_config': TimeCourseProcessConfigSchema().model_dump(),
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]'}

    def __init__(self, config=None):
        super().__init__(config=config)
        self.process = CopasiProcess(config=self.config.get('process_config'))
        self.params_to_scan = self.config.get('parameters')

    def initial_state(self):
        return self.process.initial_state()

    def inputs(self):
        return self.process.inputs()

    def outputs(self):
        return self.process.outputs()

    def update(self, state):
        """Here is where the method of perturbation differs: deterministic will use
            `np.linspace(...`
        """
        pass


class StochasticParameterScan(ParameterScan):
    """Analogous to Monte Carlo perturbations"""
    config_schema = {
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]',
        'process_config': 'tree[string]'}

    pass


def test_parameter_scan():
    pass
