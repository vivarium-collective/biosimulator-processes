"""
`Instance` API:

Higher-level API related to using the process-bigraph `Step` and/or `Process` interface.
"""


from dataclasses import dataclass
from typing import *

import matplotlib.pyplot as plt
import numpy as np
from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE
from biosimulator_processes.steps.ode_simulation import ODEProcess, CopasiStep
from biosimulator_processes.data_model import _BaseClass


def get_observables(proc: RunProcess):
    observables = []
    for port_name, port_dict in proc.process.inputs().items():
        if port_name.lower() == 'floating_species_concentrations':
            if isinstance(port_dict, dict):
                for name, typeVal in port_dict.items():
                    obs = [port_name, name]
                    observables.append(obs)
            else:
                obs = [port_name]
                observables.append(obs)
    return observables


def generate_ode_instance(process_address: str, model_fp: str, step_size: float, duration: float) -> ODEProcess:
    ode_process_config = {'model': {'model_source': model_fp}}
    proc = RunProcess(
        config={
            'process_address': process_address,
            'process_config': ode_process_config,
            'timestep': step_size,
            'runtime': duration},
        core=CORE)
    obs = get_observables(proc)

    return ODEProcess(
        address=process_address,
        model_fp=model_fp,
        observables=obs,
        step_size=step_size,
        duration=duration)


def plot_ode_output_data(data: dict, sample_size: int = None):
    time: np.ndarray = data.get('results', data['time'])
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


# TODO: use this in server
@dataclass
class ODESimulationOutput(_BaseClass):
    t: List[float]
    floating_species: Dict[str, List[float]]

    def __init__(self, data: Dict):
        self.data = data
        self.t = data['time']
        self.floating_species = {
            name: output
            for name, output in data['floating_species'].items()}

    def plot(self, sample_size: None):
        return plot_ode_output_data(self.data, sample_size=sample_size)


def run_copasi_step_from_omex(archive_dir_fp: str) -> ODESimulationOutput:
    step = CopasiStep(archive_dirpath=archive_dir_fp)
    result = step.update({})
    return ODESimulationOutput(data=result)


