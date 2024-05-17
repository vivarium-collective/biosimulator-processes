"""Comparator Process:

    Here the entrypoint is either a biomodel id or sbml model path.
"""

from typing import *
import random

import numpy as np
from process_bigraph import Process, Step

from biosimulator_processes.io import fetch_sbml_file


def mean_squared_error(data: Union[List[float], np.ndarray]) -> np.ndarray[float]:
    """Takes in an array of data which represents the results of a composition for a species/param
        at a given interval, averages the values, and then scores each item in the data array with an MSE value
        calculated against the average, returning the MSE scores as an array.

        Args:
              data:`Union[List[float, np.ndarray[float]]]`: An array of data which represents the results
                of a composition for a species/param.

        Returns:
            `np.ndarray[float]`: An array of MSE scores for each item in `data`.
    """
    if isinstance(data, list):
        data = np.array(data)
    data_average = np.mean(data)
    return (data - data_average) ** 2

  
def random_population_selection(population: List, update_population=True) -> List:
    """Pick a random member of a given population `population` and pop it from the population if
        update_population is set to True.
    """
    index = len(population) - 1
    rand_i = random.randint(0, index)
    return population.pop(rand_i) if update_population else population[rand_i]


class CompareResults(Step):
    config_schema = {
        'emitter_results'
    }


class ODEComparatorProcess(Process):
    """Process that serves to perform a comparison of ODE-enabled simulator output, particularly
        simulators that are equipped to use CVODE. Such simulators include: COPASI, Tellurium, and AMICI.
    """
    config_schema = {
        'biomodel_id': 'string',
        'duration': 'number',
        'num_steps': 'number',
        'simulators': 'list[string]',
        'framework_type': {  # TODO: handle this with assertion
            '_default': 'deterministic',
            '_type': 'string'
        },
        'target_parameter': 'maybe[tree[union[string, float]]]',  # derived from experimental data for fitness calculation
        'target_dataset': 'maybe[tree[string, tree[union[string, float]]]]'  # TODO: are experimental datasets which match the ports available?
    }

    def __init__(self, config=None, core=None):
        """
            Parameters:
                config:`Dict`: required keys include: sbml_model_file(`str`), duration(`int`),
                    num_steps(`int`), simulators(`List[str]`). Optional keys include framework_type(`str`),
                    target_parameter(`Dict`), target_dataset(`Dict`).
        """
        super().__init__(config, core)
        self.species_context_key = 'floating_species_concentrations'
        model_fp = fetch_sbml_file(self.config['biomodel_id'])
        self.simulator_instances = self._set_simulator_instances(model_fp)
        self.floating_species_ids = {}
        self.model_parameter_ids = {}
        self.reactions = {}

        # if assuming that the simulators will have the same attributes to call. TODO: ensure this happens
        for simulator_name, simulator_instance in self.simulator_instances.items():
            self.floating_species_ids[simulator_name] = simulator_instance.floating_species_list  # TODO: ensure that Tellurium has a floating_species_list
            self.model_parameter_ids[simulator_name] = simulator_instance.model_parameters_list
            self.reactions[simulator_name] = simulator_instance.reaction_list

    def initial_state(self):
        # TODO: get these values from constructor
        return {
            simulator_name: simulator_process.initial_state()
            for simulator_name, simulator_process in self.simulator_instances.items()}

    def inputs(self):
        # TODO: will each ode simulator have all of the same names/vals for this?
        input_schema = {
            simulator_name: {
                'time': 'float',
                self.species_context_key: 'tree[any]',  # floating_species_type,
                'model_parameters': 'tree[any]',  # model_params_type,
                'reactions': 'tree[any]'  # reactions_type
            }
            for simulator_name, simulator_process in self.simulator_instances.items()}

        if self.config.get('target_parameter'):
            for sim in self.simulator_instances.keys():
                input_schema[sim]['validation_score'] = {
                    '_type': 'float',
                    '_apply': 'set'}

        return input_schema

    def outputs(self):
        output_schema = {
            simulator_name: {
                'time': 'float',
                self.species_context_key: 'tree[any]'  # floating_species_type
            } for simulator_name in self.simulator_instances.keys()}

        if self.config.get('target_parameter'):
            for sim in self.simulator_instances.keys():
                output_schema[sim]['validation_score'] = {
                    '_type': 'float',
                    '_apply': 'set'}

        return output_schema

    def update(self, state, interval):
        # TODO: instantiate parallel subprocesses for the simulation run
        results = {
            simulator_name: simulator_process.update(state, interval)  # TODO: somehow integrate num_steps into interval here
            for simulator_name, simulator_process in self.simulator_instances.items()}

        # TODO: creating mapping of species names to value for MSE and iterate over below:

        if self.config.get('target_parameter'):
            target_param: dict = self.config['target_parameter']
            for simulator in self.simulator_instances.keys():
                simulator_values = results[simulator][self.species_context_key]
                simulator_result_value = simulator_values.get(target_param['name'])
                # TODO: implement MSE
                diff = mean_squared_error(target_param['value'], simulator_result_value)
                results[simulator]['validation_score'] = diff  # TODO: make this more fine-grained with MSE

        return results

    def _set_simulator_instances(self, model_fp) -> Dict:
        simulator_instances = {}
        simulators = ['tellurium', 'copasi']
        for simulator in self.config['simulators']:
            module_name = simulator + '_process'
            class_name = simulator.replace(simulator[0], simulator[0].upper()) + 'Process'
            import_statement = f'biosimulator_processes.processes.{module_name}'
            simulator_module = __import__(import_statement, fromlist=[class_name])
            simulator_instance = getattr(simulator_module, class_name)
            simulator_instances[simulator] = simulator_instance(config={
                'model': {
                    'model_source': model_fp}
            })
        return simulator_instances
