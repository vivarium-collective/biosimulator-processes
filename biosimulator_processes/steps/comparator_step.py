"""Comparator Step:

    Here the entrypoint is the results of an emitter.
"""


from tempfile import mkdtemp
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import *

from process_bigraph import Step, pp, Composite
import numpy as np
import pandas as pd

from biosimulator_processes import CORE
from biosimulator_processes.data_model import BaseModel, _BaseClass
from biosimulator_processes.data_model.compare_data_model import ParameterMSE, ODEComparisonResult
from biosimulator_processes.io import fetch_biomodel_sbml_file


@dataclass
class ProcessComparisonMatrix(_BaseClass):
    data: np.ndarray
    time_id: int


def calculate_comparison(a, b):
    return np.mean((a - b) ** 2)


# Function to construct process interval matrix
def _construct_process_interval_matrix(outputs_copasi, outputs_tellurium, outputs_amici, time_id) -> ProcessComparisonMatrix:
    comparison_matrix = np.zeros((3, 3), dtype=float)

    comparison_matrix[0, 1] = calculate_comparison(outputs_copasi, outputs_tellurium)
    comparison_matrix[0, 2] = calculate_comparison(outputs_copasi, outputs_amici)
    comparison_matrix[1, 2] = calculate_comparison(outputs_tellurium, outputs_amici)
    comparison_matrix[1, 0] = comparison_matrix[0, 1]
    comparison_matrix[2, 0] = comparison_matrix[0, 2]
    comparison_matrix[2, 1] = comparison_matrix[1, 2]

    np.fill_diagonal(comparison_matrix, 0.0)  # Diagonal can be 0.0 as there is no comparison needed
    return ProcessComparisonMatrix(data=comparison_matrix, time_id=time_id)


def _generate_ode_process_comparison_df(matrix: ProcessComparisonMatrix, simulators: list[str]) -> pd.DataFrame:
    return pd.DataFrame(matrix.data, columns=simulators, index=simulators)


def generate_ode_process_comparison_data(outputs_copasi, outputs_tellurium, outputs_amici, time_id) -> pd.DataFrame:
    simulators = ['copasi', 'tellurium', 'amici']

    # Create interval data dictionary
    interval_data = dict(zip(simulators, [outputs_copasi, outputs_tellurium, outputs_amici]))
    interval_data['time_id'] = time_id

    # Construct the matrix
    matrix = _construct_process_interval_matrix(
        outputs_copasi=interval_data['copasi'],
        outputs_tellurium=interval_data['tellurium'],
        outputs_amici=interval_data['amici'],
        time_id=interval_data['time_id'])

    return _generate_ode_process_comparison_df(matrix, simulators)


class SimulatorComparatorStep(ABC, Step):
    config_schema = {
        'model_entrypoint': 'string',  # either biomodel id or sbml filepath TODO: make from string.
        'duration': 'integer',
        'simulators': {
            '_type': 'list[string]',
            '_default': []}}

    model_entrypoint: str
    duration: int

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        source = config['model_entrypoint']
        assert 'BIO' in source or '/' in source, "You must enter either a biomodel id or path to an sbml model."

    def inputs(self):
        return {}

    def outputs(self):
        return {'comparison_data': 'tree[any]'}

    def update(self, state):
        results = self._run_composition()
        output = {'comparison_data': results}
        return output

    @abstractmethod
    def _run_composition(self, comp: Composite) -> Dict:
        pass


# TODO: Implement SED-based naming here.

class ODEComparatorStep(SimulatorComparatorStep):
    """config_schema = {'biomodel_id': 'string', 'duration': 'integer'}"""

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.model_source = self.config['model_entrypoint']
        self.duration = self.config['duration']

        model_fp = self.model_source if not self.model_source.startswith('BIO') else fetch_biomodel_sbml_file(self.model_source, save_dir=mkdtemp())
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
    def inputs(self):
        return {}

    def outputs(self):
        return {'comparison_data': 'tree[any]'}

    def update(self, state):
        comp = self._generate_composition()
        results = self._run_composition(comp)
        output = {'comparison_data': results}
        return output

    def _generate_composition(self) -> Composite:
        return Composite(config={'state': self.document}, core=CORE)

    def _run_composition(self, comp: Composite) -> Dict:
        comp.run(self.duration)
        return comp.gather_results()




