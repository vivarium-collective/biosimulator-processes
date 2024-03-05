from typing import *
from abc import abstractmethod

import numpy as np
from process_bigraph import Step
from biosimulator_processes.data_model import *
from biosimulator_processes.processes.copasi_process import CopasiProcess


class ParameterScan(Step):
    """
        For example:

            parameters = {
                'global': {
                    'ADP': <STARTING_VALUE>,
                    ...},
                'species': {
                    'species_a': <STARTING_VALUE>,
                    'species_b': ...
                    ...},
                'reactions': {
                    'R1': {
                        '(R1).k1': <STARTING_VALUE>,
                    ...}
            }

            ...according to the config schema for Copasi Process (model changes)


    """
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
    def update(self, input):
        pass


class DeterministicTimeCourseParameterScan(ParameterScan):
    """Using CopasiProcess as the primary TimeCourse simulator.

        # TODO: enable multiple Simulator types.

        should at some point in the stack return a list or dict of configs that can be used by CopasiProcess which are then
            used to run during update
    """
    config_schema = {
        'process_config': TimeCourseProcessConfigSchema().model_dump(),
        'n_iterations': 'int',
        'perturbation_magnitude': 'float',
        'parameters': 'list[object]'}

    def __init__(self, config=None):
        super().__init__(config=config)
        self.process = CopasiProcess(config=self.config.get('process_config'))
        self.params_to_scan: List[ModelParameter] = self.config.get('parameters', [])
        self.n_iterations = self.config['n_iterations']


    def initial_state(self):
        return {
            str(n): self.process.initial_state()
            for n in range(self.n_iterations)}

    def inputs(self):
        return self.process.inputs()

    def outputs(self):
        return {
            str(n): self.process.outputs()
            for n in range(self.n_iterations)}

    def update(self, input):
        """Here is where the method of perturbation differs: deterministic will use
            `np.linspace(...`
        """
        # set up parameters
        results = {}
        scan_range = np.linspace(0, self.n_iterations, self.config['perturbation_magnitude'])
        for n in scan_range:
            interval = input['time']
            for param in self.params_to_scan:
                if 'global' in param.scope:
                    pass
                elif 'species' in param.scope:
                    for species_id, species_value in input['floating_species']:
                        if param.name in species_id:
                            input['floating_species'][species_id] = n
                r = self.process.update(
                    inputs=input,
                    interval=interval)
                results[str(n)] = r
        return results



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
