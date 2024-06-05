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


class UtcComparisonDocument(dict):
    def __new__(cls, model_source: str, *args, **kwargs):
        """Document factory for composite simulations related to the comparison
            of Uniform Time Course simulator outputs. Inherits from the python built-in `dict`
            factory.
        """
        # TODO: support more config options.
        utc_comparison_document = {
            'amici': {
                '_type': 'step',
                'address': 'local:utc-amici',
                'config': {
                    'model': {
                        'model_source': model_source
                    }
                },
                'inputs': {
                    'time': ['time_store'],
                    'floating_species': ['amici_floating_species_store'],
                    'model_parameters': ['amici_model_parameters_store'],
                    'reactions': ['amici_reactions_store']
                },
                'outputs': {
                    'time': ['time_store'],
                    'floating_species': ['amici_floating_species_store']
                }
            },
            'copasi': {
                '_type': 'step',
                'address': 'local:utc-copasi',
                'config': {
                    'model': {
                        'model_source': model_source
                    }
                },
                'inputs': {
                    'time': ['time_store'],
                    'floating_species': ['copasi_floating_species_store'],
                    'model_parameters': ['copasi_model_parameters_store'],
                    'reactions': ['copasi_reactions_store']
                },
                'outputs': {
                    'time': ['time_store'],
                    'floating_species': ['copasi_floating_species_store']
                }
            },
            'tellurium': {
                '_type': 'step',
                'address': 'local:utc-tellurium',
                'config': {
                    'model': {
                        'model_source': model_source
                    }
                },
                'inputs': {
                    'time': ['time_store'],
                    'floating_species': ['tellurium_floating_species_store'],
                    'model_parameters': ['tellurium_model_parameters_store'],
                    'reactions': ['tellurium_reactions_store']
                },
                'outputs': {
                    'time': ['time_store'],
                    'floating_species': ['tellurium_floating_species_store']
                }
            },
            'comparison': {
                '_type': 'step',
                'address': 'local:utc-comparator',
                'config': {
                    'simulators': ['amici', 'copasi', 'tellurium'],
                },
                'inputs': {
                    'time': ['time_store'],
                    'amici_floating_species': ['amici_floating_species_store'],
                    'copasi_floating_species': ['copasi_floating_species_store'],
                    'tellurium_floating_species': ['tellurium_floating_species_store'],
                },
                'outputs': {
                    'results': ['results_store'],
                }
            },
            'emitter': {
                '_type': 'step',
                'address': 'local:ram-emitter',
                'config': {
                    'emit': {
                        'results': 'tree[string]',
                    }
                },
                'inputs': {
                    'results': ['results_store'],
                }
            }
        }


        utc_comparison_output_bridge = {
            'inputs': {
                'results': ['results_store']
            },
            'outputs': {
                'results': ['results_store']
            }
        }

        return {'state': utc_comparison_document, 'bridge': utc_comparison_output_bridge}


