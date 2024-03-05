from typing import *
from abc import abstractmethod
from process_bigraph import Step


class ParameterScan(Step):
    config_schema = {
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]',  # ie: 'param_type: param_name'... like 'global': 'ADP', 'species': 'S3'
        'process_instance': 'object'}  # use the builder to extract this
        # 'process_instances': 'tree[object]'

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


class DeterministicParameterScan(ParameterScan):
    config_schema = {
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]',
        'process_instance': 'object'}  # use the builder to extract this
    
    def __init__(self):
        super().__init__()
    
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


class StochasticParameterScan(ParameterScan):
    config_schema = {
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'tree[string]',
        'process_instance': 'object'}  # use the builder to extract this

    def __init__(self):
        super().__init__()

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
