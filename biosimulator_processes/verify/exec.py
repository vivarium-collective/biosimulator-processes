from typing import Dict

import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from biosimulator_processes.data_model.compare_data_model import ODEProcessIntervalComparison


def generate_ode_process_interval_comparison_data(outputs: list[np.array], time_id: int) -> ODEProcessIntervalComparison:
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


def plot_ode_process_comparison(
        mse_df: pd.DataFrame,
        rmse_df: pd.DataFrame,
        inner_product_df: pd.DataFrame,
        outer_product_matrices: Dict
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
