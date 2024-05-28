from typing import Dict

from numpy import ndarray
import matplotlib.pyplot as plt
from process_bigraph import Composite

from biosimulator_processes import CORE


class Workflow(Composite):
    # TODO: finish this.
    def __init__(self, config=None, core=None):
        super().__init__(config, core)


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


def run_ode_steps_from_omex(archive_dir_fp: str):
    ode_simulators = ['copasi', 'tellurium', 'amici']
    sim_doc = {}
    for ode_sim in ode_simulators:
        sim_doc[ode_sim] = {
                'address': f'local:{ode_sim}',
                '_type': 'step',
                'config': {
                    'archive_filepath': 'archive_dir_fp'
                },
                'inputs': {},
                'outputs': {
                    'time': ['time_store'],
                    'floating_species': ['floating_species_store'],
                }
        }
    bridge = {'inputs': {}, 'outputs': {'time': ['time_store'], 'floating_species': ['floating_species_store']}}
    wf = Workflow(config={'state': sim_doc, 'bridge': bridge}, core=CORE)
    wf.run(0)
    print(wf.gather_results())

