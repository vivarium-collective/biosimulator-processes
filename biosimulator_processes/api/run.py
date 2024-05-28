from typing import Dict

from numpy import ndarray
import matplotlib.pyplot as plt

from biosimulator_processes.steps.ode_simulation import CopasiStep, TelluriumStep, AmiciStep


def plot_ode_output_data(data: Dict, sample_size: int = None) -> None:
    time: ndarray = data.get('results', data['time'])
    plt.figure(figsize=(20, 8))
    for name, output in data['floating_species'].items():
        x = time[:sample_size] if sample_size else time
        y = output[:sample_size] if sample_size else output
        plt.plot(x, y, label=name)

    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title('Species Concentrations Over Time')
    plt.legend()
    plt.grid(True)
    # plt.xlim([0, time[-1]])  # Set x-axis limits from 0 to the last time value
    # plt.ylim([min([list(v.values())[0] for v in spec_outputs]), max([list(v.values())[0] for v in spec_outputs])])  # Adjust y-axis to fit all data
    plt.show()


def run_ode_step_from_omex(archive_dir_fp: str, simulator_name: str):
    ode_simulators = ['copasi', 'tellurium', 'amici']
    for ode_sim in ode_simulators:
        if simulator_name.lower() in ode_sim:
            pass



def run_copasi_step_from_omex(archive_dir_fp: str):
    step = CopasiStep(archive_dirpath=archive_dir_fp)
    result = step.update({})
    return ODESimulationOutput(data=result)
