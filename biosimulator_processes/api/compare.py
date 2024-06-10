from typing import *
import os

import numpy as np
import pandas as pd

from biosimulator_processes.data_model.compare_data_model import ComparisonMatrix
from biosimulator_processes.io import read_report_outputs


__all__ = [
    'generate_comparison',
    'exec_compare'
]


def generate_utc_species_comparison(outputs: List[np.ndarray], species_name, simulators, method=None):
    methods = [method] if method is not None else ['mse', 'prox']
    results = dict(zip(
        methods,
        list(map(
            lambda m: generate_species_comparison_matrix(outputs=outputs, simulators=simulators, method=m).to_dict(),
            methods
        ))
    ))
    # results['output_data'] = {}
    # for simulator_name in outputs.keys():
    #     simulator_vals = list(outputs[simulator_name].values())
    #     for i, spec in enumerate(outputs[simulator_name].keys()):
    #         if spec in species_name:
    #             results['output_data'][simulator_name] = simulator_vals[i].tolist()
    # results['species_name'] = species_name
    return results


def _get_output_stack(outputs: dict, spec_id: str):
    output_stack = []
    for sim_name in outputs.keys():
        sim_data = outputs[sim_name]['data']
        for data_index, data in enumerate(sim_data):
            data_id = data['dataset_label']
            if data_id == spec_id:
                print(spec_id, data_id)
                output_stack.append(sim_data[data_index]['data'])
            else:
                pass
    return np.stack(output_stack)



def write_utc_comparison_reports(
        save_dir: str,
        sbml_species_mapping: dict,
        copasi_results: dict,
        amici_results: dict,
        tellurium_results: dict,
        ground_truth_results: dict = None,
        method='prox') -> None:
    """Generate a comparison between copasi, tellurium, and amici outputs. Add an optional ground_truth to the comparison. Please NOTE: all results
        must be formatted as a dict, where: {'time': [...], 'floating_species': {spec_id: [...]}}. The corresponds to the result format of Utc process
        results.

            Args:
                save_dir (:obj:`str`): working directory in which to save
                sbml_species_mapping (:obj:`dict`): sbml species mapping in which keys are species names, and values are the references of the key names
                    within the SBML modeling standard.
                copasi_results (:obj:`dict`): copasi results
                tellurium_results (:obj:`dict`): tellurium results
                amici_results (:obj:`dict`): amici results
                ground_truth_results (:obj:`dict`): ground truth results
                method (:obj:`str`): method with which to generate the comparison matrix data. One of: `'mse'` or `'prox'`. Defaults to the
                    prox method which returns a boolean of value proximities given a tolerance.
    """
    for spec_name, sbml_id in sbml_species_mapping.items():
        outputs = [copasi_results['floating_species'][spec_name], amici_results['floating_species'][spec_name], tellurium_results['floating_species'][spec_name]]
        comparison = generate_comparison(
            outputs=outputs,
            simulators=['copasi', 'amici', 'tellurium'],
            ground_truth=ground_truth_results['floating_species'][spec_name],
            method=method,
            matrix_id=f'{spec_name.replace(" ", "_")}_comparison')
        if not os.path.exists(save_dir):
            os.mkdir(save_dir)
        comparison.data.to_csv(os.path.join(save_dir, f'{comparison.name}.csv'))


def exec_compare(reports_path: str, process_results: dict, save_dir: str):
    """Execute a comparison against an individual process results against a ground truth
        whose origin resides in the reports path. TODO: More carefully index this report
        data using species ids in the processes.
    """
    if not os.path.exists(save_dir):
        os.mkdir(save_dir)

    species_outputs = process_results.get('floating_species_concentrations', 'floating_species')
    species_ids = list(species_outputs.keys())
    process_output_vals = [
        v for k, v in species_outputs.items()
    ]
    report_outputs = read_report_outputs(reports_path)
    report_outputs.data.pop(0)  # remove for time
    ground_truth = np.stack([output.data for output in report_outputs.data])
    for i, truth in enumerate(ground_truth):
        v = [process_output_vals[i]]
        comparison = generate_comparison(
            outputs=[process_output_vals[i]],
            simulators=['amici'],
            method='mse',
            ground_truth=truth,
            matrix_id=f'truth_{i}')
        comparison.data.to_csv(os.path.join(save_dir, comparison.name) + '.csv')


# exec comparisons used at high level
def generate_comparison(
        outputs: List[np.ndarray],
        simulators: List[str],
        method: Union[str, any] = 'prox',
        rtol: float = None,
        atol: float = None,
        ground_truth: np.ndarray = None,
        matrix_id: str = None
        ) -> ComparisonMatrix:
    """Generate a Mean Squared Error comparison matrix of arr1 and arr2, indexed by simulators by default,
            or an AllClose Tolerance routine result if `method` is set to `prox`.

            Args:
                outputs: list of output arrays.
                simulators: list of simulator names.
                matrix_id: name/id of the comparison
                method: pass one of either: `mse` to perform a mean-squared error calculation
                    or `prox` to perform a pair-wise proximity tolerance test using `np.allclose(outputs[i], outputs[i+1])`.
                rtol:`float`: relative tolerance for comparison if `prox` is used.
                atol:`float`: absolute tolerance for comparison if `prox` is used.
                ground_truth: If passed, this value is compared against each simulator in simulators. Currently, this
                    field is agnostic to any verified/validated source, and we trust that the user has verified it. Defaults
                    to `None`.

            Returns:
                ComparisonMatrix object consisting of:
                    - `name`: the id of the matrix
                    - `data`: Pandas dataframe representing a comparison matrix where `i` and `j` are both indexed by the
                        simulators involved. The aforementioned simulators involved will also include the `ground_truth` value
                        within the indices if one is passed.
                    - `ground_truth`: Reference to the ground truth vals if used.
    """
    matrix_data = generate_matrix_data(outputs, simulators, method, rtol, atol, ground_truth)
    return ComparisonMatrix(name=matrix_id, data=matrix_data, ground_truth=ground_truth)


# comparison methods
def calculate_mse(a, b) -> int:
    return np.mean((a - b) ** 2)


def compare_arrays(arr1: np.ndarray, arr2: np.ndarray, atol=None, rtol=None) -> bool:
    """Original methodology copied from biosimulations runutils."""
    if isinstance(arr1[0], np.float64):
        max1 = max(arr1)
        max2 = max(arr2)
        aTol = atol or max(1e-3, max1*1e-5, max2*1e-5)
        rTol = rtol or 1e-4
        return np.allclose(arr1, arr2, rtol=rTol, atol=aTol)

    for n in range(len(arr1)):
        if not compare_arrays(arr1[n], arr2[n]):
            return False
    return True


def generate_matrix_data(
    outputs: List[np.ndarray],
    simulators: List[str],
    method: Union[str, any] = 'prox',
    rtol: float = None,
    atol: float = None,
    ground_truth: np.ndarray = None
    ) -> pd.DataFrame:
    """Generate a Mean Squared Error comparison matrix of arr1 and arr2, indexed by simulators by default,
        or an AllClose Tolerance routine result if `method` is set to `prox`.

        Args:
            outputs: list of output arrays.
            simulators: list of simulator names.
            method: pass one of either: `mse` to perform a mean-squared error calculation
                or `prox` to perform a pair-wise proximity tolerance test using `np.allclose(outputs[i], outputs[i+1])`.
            rtol:`float`: relative tolerance for comparison if `prox` is used.
            atol:`float`: absolute tolerance for comparison if `prox` is used.
            ground_truth: If passed, this value is compared against each simulator in simulators. Currently, this
                field is agnostic to any verified/validated source, and we trust that the user has verified it. Defaults
                to `None`.

        Returns:
            Pandas dataframe representing a comparison matrix where `i` and `j` are both indexed by the
                simulators involved. The aforementioned simulators involved will also include the `ground_truth` value
                within the indices if one is passed.
    """

    # TODO: map arrs to simulators more tightly.
    if ground_truth is not None:
        simulators.append('ground_truth')
        outputs.append(ground_truth)

    use_tol_method = method.lower() == 'prox'
    matrix_dtype = float if not use_tol_method else bool
    num_simulators = len(simulators)
    mse_matrix = np.zeros((num_simulators, num_simulators), dtype=matrix_dtype)

    # fill the matrices with the calculated values
    for i in range(len(simulators)):
        for j in range(i, len(simulators)):
            output_i = outputs[i]
            output_j = outputs[j]
            method_type = method.lower()

            result = calculate_mse(output_i, output_j) if method_type == 'mse' else compare_arrays(output_i, output_j, rtol, atol) if use_tol_method else None
            assert result is not None, "You must pass a valid method argument value of either mse or tol"
            # mse_matrix[i, j] = calculate_mse(output_i, output_j) if not use_tol_method else compare_arrays(output_i, output_j, rtol, atol)

            mse_matrix[i, j] = result
            if i != j:
                mse_matrix[j, i] = mse_matrix[i, j]

    return pd.DataFrame(mse_matrix, index=simulators, columns=simulators)


def generate_species_comparison_matrix(
    outputs: Union[np.ndarray, List[np.ndarray]],
    simulators: List[str],
    method: Union[str, any] = 'prox',
    rtol: float = None,
    atol: float = None,
    ground_truth: np.ndarray = None
) -> pd.DataFrame:
    """Generate a Mean Squared Error comparison matrix of arr1 and arr2, indexed by simulators by default,
        or an AllClose Tolerance routine result if `method` is set to `prox`.

        Args:
            outputs: list of output arrays.
            simulators: list of simulator names.
            method: pass one of either: `mse` to perform a mean-squared error calculation
                or `prox` to perform a pair-wise proximity tolerance test using `np.allclose(outputs[i], outputs[i+1])`.
            rtol:`float`: relative tolerance for comparison if `prox` is used.
            atol:`float`: absolute tolerance for comparison if `prox` is used.
            ground_truth: If passed, this value is compared against each simulator in simulators. Currently, this
                field is agnostic to any verified/validated source, and we trust that the user has verified it. Defaults
                to `None`.

        Returns:
            Pandas dataframe representing a comparison matrix where `i` and `j` are both indexed by the
                simulators involved. The aforementioned simulators involved will also include the `ground_truth` value
                within the indices if one is passed.
    """

    # TODO: implement the ground truth
    _simulators = simulators.copy()
    _outputs = outputs.copy()
    if ground_truth is not None:
        _simulators.append('ground_truth')
        _outputs.append(ground_truth)

    use_tol_method = method.lower() == 'prox'
    matrix_dtype = np.float64 if not use_tol_method else bool
    num_simulators = len(_simulators)
    mse_matrix = np.zeros((num_simulators, num_simulators), dtype=matrix_dtype)

    # fill the matrices with the calculated values
    for i in range(len(_simulators)):
        for j in range(i, len(_simulators)):
            output_i = _outputs[i]
            output_j = _outputs[j]
            method_type = method.lower()
            result = calculate_mse(output_i, output_j) if method_type == 'mse' else compare_arrays(arr1=output_i, arr2=output_j, rtol=rtol, atol=atol)

            mse_matrix[i, j] = result
            if i != j:
                mse_matrix[j, i] = mse_matrix[i, j]

    return pd.DataFrame(mse_matrix, index=_simulators, columns=_simulators)

