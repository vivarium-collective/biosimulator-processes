from typing import Dict, Union

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from process_bigraph import Process

from biosimulator_processes.data_model.compare_data_model import ODEProcessIntervalComparison, ODEComparisonResult
from biosimulator_processes.data_model.verify_data_model import OutputAspectVerification
from biosimulator_processes.services.rest_service import BiosimulationsRestService


# *VERIFICATION*å
def _is_equal(a, b):
    if isinstance(a, list):
        a = np.array(a)
    if isinstance(b, list):
        b = np.array(b)

    return np.allclose(a, b)


def is_equal(a, b) -> bool:
    return a == b or b == a


def create_ode_process_instance(process_name: str, biomodel_id=None, sbml_model_file=None) -> Process:
    module_name = f'{process_name}_process'
    import_statement = f'biosimulator_processes.processes.{module_name}'
    module_paths = module_name.split('_')
    class_name = module_paths[0].replace(module_name[0], module_name[0].upper())
    class_name += module_paths[1].replace(module_paths[1][0], module_paths[1][0].upper())
    module = __import__(
        import_statement, fromlist=[class_name])
    model_source = biomodel_id or sbml_model_file
    bigraph_class = getattr(module, class_name)
    return bigraph_class(config={'model': {'model_source': model_source}})


def verify_ode_process_outputs(process_name: str, target_report_fp: str, biomodel_id: str = None, sbml_model_file: str = None):
    process = create_ode_process_instance(process_name, biomodel_id, sbml_model_file)
    process_keys = list(process.inputs()['floating_species_concentrations'].keys())

    report_outputs = BiosimulationsRestService().read_report_outputs(report_file_path=target_report_fp)

    names_verification = verify_ode_process_output_names(process_name, target_report_fp, biomodel_id, sbml_model_file)

    # TODO: here, read the SEDML file to determine the duration of time used for expected results.
    for d in report_outputs.data:
        print(f'Species: {d.dataset_label}, Num points: {len(d.data)}')

    # TODO: iterate over d.data length to infer number of steps used in original simulation.


# TODO: make this more general
def verify_ode_process_output_names(process_name: str, source_report_fp: str, biomodel_id: str = None, sbml_model_file: str = None) -> OutputAspectVerification:
    # Get the class from the module
    # TODO: Automatically generate this from the biosimulations rest server
    process = create_ode_process_instance(process_name, biomodel_id, sbml_model_file)
    process_keys = list(process.inputs()['floating_species_concentrations'].keys())

    report_outputs = BiosimulationsRestService().read_report_outputs(report_file_path=source_report_fp)
    report_keys = [datum.dataset_label for datum in report_outputs.data]
    for i, val in enumerate(report_keys):
        if report_keys[i].lower() == 'time':
            report_keys.pop(i)

    return OutputAspectVerification(
        aspect_type='names',
        is_verified=is_equal(report_keys, process_keys),
        expected_data=report_keys,
        process_data=process_keys)


def transform_data(data: list[float], r: tuple, data_type: str = 'float64') -> np.ndarray:
    """Transform the `data` to fit range `r`, where `r=(rangeStart, rangeStop)`"""
    min_orig = min(data)
    max_orig = max(data)
    s, e = r[0], r[1]
    normalized_data = [s + ((x - min_orig) * (e - s) / (max_orig - min_orig)) for x in data]
    return np.array(normalized_data, dtype=data_type)


# *COMPARISONS*
def generate_interval_comparisons(ode_process_comparison_output: ODEComparisonResult):
    all_comparison_data = []

    for interval_output in ode_process_comparison_output.outputs:
        time_id = interval_output.interval_id
        interval_output_attributes = vars(interval_output)

        concentrations_data = []
        for output_key, output_value in interval_output_attributes.items():
            if 'concentrations' in output_key:
                process_interval_output = np.array(list(interval_output_attributes[output_key].values()))
                concentrations_data.append(process_interval_output)
            if isinstance(output_value, dict):
                process_outputs = list(output_value.values())

        interval_comparison = generate_ode_process_interval_comparison_data(outputs=concentrations_data, time_id=time_id)
        all_comparison_data.append(interval_comparison)

    return all_comparison_data


def generate_ode_process_interval_comparison_data(outputs: list[np.array], time_id: Union[float, int]) -> ODEProcessIntervalComparison:
    simulators = ['copasi', 'tellurium', 'amici']

    mse_matrix = np.zeros((3, 3), dtype=float)
    rmse_matrix = np.zeros((3, 3), dtype=float)
    inner_product_matrix = np.zeros((3, 3), dtype=float)
    outer_product_matrices = {}

    # fill the matrices with the calculated values
    for i in range(len(simulators)):
        for j in range(i, len(simulators)):
            mse_matrix[i, j] = calculate_mse(outputs[i], outputs[j])
            rmse_matrix[i, j] = calculate_rmse(outputs[i], outputs[j])
            inner_product_matrix[i, j] = calculate_inner_product(outputs[i], outputs[j])
            outer_product_matrices[(simulators[i], simulators[j])] = calculate_outer_product(outputs[i], outputs[j])
            if i != j:
                mse_matrix[j, i] = mse_matrix[i, j]
                rmse_matrix[j, i] = rmse_matrix[i, j]
                inner_product_matrix[j, i] = inner_product_matrix[i, j]

    # convert matrices to dataframes for better visualization
    mse_df = pd.DataFrame(mse_matrix, index=simulators, columns=simulators)
    rmse_df = pd.DataFrame(rmse_matrix, index=simulators, columns=simulators)
    inner_product_df = pd.DataFrame(inner_product_matrix, index=simulators, columns=simulators)

    return ODEProcessIntervalComparison(
        mse_data=mse_df,
        rmse_data=rmse_df,
        inner_prod_data=inner_product_df,
        outer_prod_data=outer_product_matrices,
        time_id=time_id)


def generate_comparison_matrix(arr1: np.ndarray, arr2: np.ndarray, *simulators: str, use_tol: bool = False) -> pd.DataFrame:
    """Generate a Mean Squared Error comparison matrix of arr1 and arr2, indexed by simulators by default, or an AllClose Tolerance routine if `use_tol` is set to true."""

    # TODO: map arrs to simulators more tightly.
    mse_matrix = np.zeros((3, 3), dtype=float)
    outputs = [arr1, arr2]

    # fill the matrices with the calculated values
    for i in range(len(simulators)):
        for j in range(i, len(simulators)):
            mse_matrix[i, j] = calculate_mse(outputs[i], outputs[j])
            if i != j:
                mse_matrix[j, i] = mse_matrix[i, j]

    return pd.DataFrame(mse_matrix, index=simulators, columns=simulators)


def plot_ode_process_comparison(
        mse_df: pd.DataFrame,
        rmse_df: pd.DataFrame,
        inner_product_df: pd.DataFrame,
        outer_product_matrices: Dict,
        show_outer=False
        ) -> None:
    # plot heatmaps for MSE, RMSE, and inner product matrices
    plt.figure(figsize=(15, 5))

    plt.subplot(1, 3, 1)
    sns.heatmap(mse_df, annot=True, cmap="coolwarm", cbar=True)
    plt.title("MSE Matrix")

    plt.subplot(1, 3, 2)
    sns.heatmap(rmse_df, annot=True, cmap="coolwarm", cbar=True)
    plt.title("RMSE Matrix")

    plt.subplot(1, 3, 3)
    sns.heatmap(inner_product_df, annot=True, cmap="coolwarm", cbar=True)
    plt.title("Inner Product Matrix")

    plt.tight_layout()
    plt.show()

    if show_outer:
        # visualize outer product matrices
        fig, axes = plt.subplots(3, 3, figsize=(15, 15))
        for idx, ((sim1, sim2), matrix) in enumerate(outer_product_matrices.items()):
            ax = axes[idx // 3, idx % 3]
            sns.heatmap(matrix, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, cbar=True)
            ax.set_title(f"Outer Product: {sim1} vs {sim2}")
            ax.set_xlabel(sim2)
            ax.set_ylabel(sim1)

        plt.tight_layout()
        plt.show()


def calculate_mse(a, b):
    return np.mean((a - b) ** 2)


def calculate_rmse(a, b):
    return np.sqrt(calculate_mse(a, b))


def calculate_inner_product(a, b) -> np.ndarray:
    return np.dot(a, b)


def calculate_outer_product(a, b) -> np.ndarray:
    return np.outer(a, b)
