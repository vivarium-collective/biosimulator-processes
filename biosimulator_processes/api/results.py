from typing import Tuple

import numpy as np


def infer_slice(t: np.ndarray, output_start_time: int, tol: float = 0.9) -> tuple[int, int]:
    slice_start_index = 0
    slice_end_index = 0
    for i, n in enumerate(t):
        if output_start_time - tol <= round(n) <= output_start_time + tol:
            slice_start_index = i - 1
        if n == t[-1]:
            slice_end_index = i + 1
    return (slice_start_index, slice_end_index)


def plot_utc_outputs(data: dict, t: Union[np.array, List[float]], x=None, y=None) -> None:
    """Plot ODE simulation observables with Seaborn."""
    plt.figure(figsize=(20, 8))
    species_data = data.get('floating_species') or data.get('floating_species_concentrations')
    for spec_name, spec_data in species_data.items():
        sns.lineplot(x=t, y=spec_data)
    plt.show()


def plot_ode_output_data(data: dict, simulator_name: str, sample_size: int = None) -> None:
    """
    Args:
        data: outermost keys are 'time' and 'floating_species'

    Returns:

    """
    time: np.ndarray = data.get('results', data['time'])
    plt.figure(figsize=(20, 8))
    for name, output in data.get('floating_species', 'floating_species_concentrations').items():
        x = np.array(time)
        y = output
        plt.plot(x, y, label=name)

    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title(f'Species Concentrations Over Time with {simulator_name}')
    plt.legend()
    plt.grid(True)
    # plt.xlim([0, time[-1]])  # Set x-axis limits from 0 to the last time value
    # plt.ylim([min([list(v.values())[0] for v in spec_outputs]), max([list(v.values())[0] for v in spec_outputs])])  # Adjust y-axis to fit all data
    plt.show()
