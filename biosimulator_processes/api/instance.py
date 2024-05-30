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




