"""Comparator Step:

    Here the entrypoint is the results of an emitter.
"""


from tempfile import mkdtemp
from abc import abstractmethod
from typing import *

from process_bigraph import Step, pp, Composite
import numpy as np

from biosimulator_processes import CORE
from biosimulator_processes.data_model import BaseModel
from biosimulator_processes.data_model.compare_data_model import ParameterMSE, ODEComparisonResult
from biosimulator_processes.io import fetch_sbml_file


class ParameterMSEValues(BaseModel):
    param_id: str
    values: List[float]


class RMSE:
    def __init__(self, values: List[float], param_id: str):
        self.param_id = param_id
        self.mse_values = self._calculate_mse_values(values)
        self.value = self._calculate_rmse(values)

    def _calculate_mse_values(self, values: List[float]) -> ParameterMSEValues:
        values_array = np.array(values)
        mean_value = np.mean(values_array)
        mse_values = (values_array - mean_value) ** 2
        return ParameterMSEValues(values=mse_values.tolist(), param_id=self.param_id)

    def _calculate_rmse(self, values: List[float]) -> float:
        all_mse_values = self._calculate_mse_values(values)
        mean_mse = np.mean(self.mse_values.values)
        rmse = np.sqrt(mean_mse)
        return rmse


def calculate_mse_for_simulator_param(values: Dict[str, float], param_name: str) -> List[ParameterMSE]:
    """Calculate the MSE for a given set of simulator parameter outputs whose description are identical. For example, for a given
        parameter 'T': {'copasiA': 3.3, 'tellurium1': 3.2, 'amici_simple': 3.12}

        Args:
              values:`Dict[str, float]`: for a given parameter, a mapping of each simulator process id within a bigraph
                to its version of the output.
              param_name:`str`: name of the given parameter

    """
    vals = np.array(list(values.values()))
    mean = np.mean(vals)
    mse_vals = (vals - mean) ** 2
    process_names = list(values.keys())
    mse_dict = dict(zip(process_names, mse_vals.tolist()))
    return [ParameterMSE(param_name=param_name, value=mse_value, mean=mean, process_id=sim_name) for sim_name, mse_value in mse_dict.items()]


def comparison(a, b, rTol, aTol) -> int:
    return int(np.allclose(a, b, rTol, aTol))


def calc_comparison(a, b):
    return (a - b) ** 2


def generate_pairwise_comparison(data):
    """
        Args:
            data:`np.ndarray`: shape of (n, 2) where 2 represents the outputs to two simulators.

    """
    comparison_data = {}
    transposed = data.transpose()
    for i, param_compare in enumerate(transposed):
        comparison_data['param_' + str(i)] = calc_comparison(*param_compare)
    return comparison_data


class SimulatorComparatorStep(Step):
    config_schema = {
        'biomodel_id': 'string',
        'duration': 'integer',
        'simulators': {
            '_type': 'list[string]',
            '_default': []}}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.biomodel_id = self.config['biomodel_id']
        self.duration = self.config['duration']

    def inputs(self):
        return {}

    def outputs(self):
        return {'comparison_data': 'tree[any]'}

    def update(self, state):
        results = self._run_workflow()
        output = {'comparison_data': results}
        return output


class ODEComparatorStep(SimulatorComparatorStep):
    """config_schema = {'biomodel_id': 'string', 'duration': 'integer'}"""

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.biomodel_id = self.config['biomodel_id']
        self.duration = self.config['duration']

        directory = mkdtemp()
        model_fp = fetch_sbml_file(self.biomodel_id, save_dir=directory)
        self.document = {
            'copasi_simple': {
                '_type': 'process',
                'address': 'local:copasi',
                'config': {'model': {'model_source': model_fp}},
                'inputs': {'floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                           'model_parameters': ['model_parameters_store'],
                           'time': ['time_store'],
                           'reactions': ['reactions_store']},
                'outputs': {'floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                            'time': ['time_store']}
            },
            'amici_simple': {
                '_type': 'process',
                'address': 'local:amici',
                'config': {'model': {'model_source': model_fp}},
                'inputs': {
                    'floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                    'model_parameters': ['model_parameters_store'],
                    'time': ['time_store'],
                    'reactions': ['reactions_store']},
                'outputs': {
                    'floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                    'time': ['time_store']}
            },
            'emitter': {
                '_type': 'step',
                'address': 'local:ram-emitter',
                'config': {
                    'emit': {
                        'copasi_simple_floating_species_concentrations': 'tree[float]',
                        'amici_simple_floating_species_concentrations': 'tree[float]',
                        'tellurium_simple_floating_species_concentrations': 'tree[float]',
                        'time': 'float'
                    }
                },
                'inputs': {
                    'copasi_simple_floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                    'amici_simple_floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                    'tellurium_simple_floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                    'time': ['time_store']
                }
            },
            'tellurium_simple': {
                '_type': 'process',
                'address': 'local:tellurium',
                'config': {'model': {'model_source': model_fp}},
                'inputs': {'floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                           'model_parameters': ['model_parameters_store'],
                           'time': ['time_store'],
                           'reactions': ['reactions_store']},
                'outputs': {'floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                            'time': ['time_store']}}}

    # TODO: Do we need this?
    # def inputs(self):
    #     return {}

    # def outputs(self):
    #     return {'comparison_data': 'tree[any]'}

    def update(self, state):
        comp = self._generate_composition(self.document)
        results = self._run_composition(comp)
        output = {'comparison_data': results}
        return output

    @staticmethod
    def _generate_composition(document: Dict) -> Composite:
        return Composite(config={'state': document}, core=CORE)

    def _run_composition(self, comp: Composite) -> Dict:
        comp.run(self.duration)
        return comp.gather_results()


def compare_simulators(output1, output2, rtol=1e-2, atol=1e-3):
    return np.allclose(output1, output2, rtol=rtol, atol=atol)


def populate_comparison_matrix(ode_comparison_results: ODEComparisonResult):
    for interval_output in ode_comparison_results.outputs:
        pass


# TODO: normalize data prior


def calculate_comparison(a, b):
    return np.sum((a - b) ** 2)


def calculate_comparison_scores(comparison_matrix):
    return [np.sum(comparison_matrix[i]) / 3 for i in range(3)]


def construct_process_interval_matrix(outputs_copasi, outputs_amici, outputs_tellurium, time_id, rtol=None, atol=None) -> np.ndarray:
    comparison_matrix = np.zeros((3, 3), dtype=float)

    comparison_matrix[0, 1] = calculate_comparison(outputs_copasi, outputs_tellurium)
    comparison_matrix[0, 2] = calculate_comparison(outputs_copasi, outputs_amici)
    comparison_matrix[1, 2] = calculate_comparison(outputs_tellurium, outputs_amici)
    comparison_matrix[1, 0] = comparison_matrix[0, 1]
    comparison_matrix[2, 0] = comparison_matrix[0, 2]
    comparison_matrix[2, 1] = comparison_matrix[1, 2]

    np.fill_diagonal(comparison_matrix, True)
    return comparison_matrix


def generate_process_comparison_scores(
        outputs_copasi,
        outputs_amici,
        outputs_tellurium,
        time_id,
        rtol=1e-2,
        atol=1e-3):
    # TODO: use ODEComparisonResult to populate args
    comparison_matrix = construct_process_interval_matrix(
        outputs_copasi,
        outputs_amici,
        outputs_tellurium,
        time_id,
        rtol,
        atol)

    scores = calculate_comparison_scores(comparison_matrix)
    print("Scores for each simulator:", scores)

    return scores


