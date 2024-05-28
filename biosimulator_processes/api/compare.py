from typing import *
import os

import numpy as np
import pandas as pd

from biosimulator_processes.data_model.compare_data_model import ComparisonMatrix


__all__ = [
    'generate_comparison'
]


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
    mse_matrix = np.zeros((3, 3), dtype=matrix_dtype)

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
