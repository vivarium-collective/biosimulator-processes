from dataclasses import dataclass
from typing import *

from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE
from biosimulator_processes.data_model import _BaseClass


class ODEProcess(RunProcess):
    def __init__(self, config=None, core=None):
        super().__init__(config, core)

    def run(self, input_state=None):
        return self.update(input_state or {})


@dataclass
class ProcessObservable(_BaseClass):
    path_root: str
    root_children: list[str]
    path: list[str] = None

    def __post_init__(self):
        self.path = [self.path_root, *self.root_children]


def generate_ode_process_instance(
        entrypoint: Union[str, dict[str, any]],  # either sbml model path or sed_model dict which conforms to the spec in sed data model in this repo.
        process_address: str,
        observables: List[str],
        step_size: float,
        duration: float,
        **process_config
) -> ODEProcess:
    """Generate loaded ode process.

        Args:
            entrypoint (Union[str, dict[str, any]]): either sbml model path or sed_model dict which conforms to the spec in sed data model in this repo.
            process_address (str): the address in registry of the process to be loaded as per the CORE registry
            observables (list[str]): observables to be loaded in path form
            step_size (float): the step size in seconds
            duration (float): the duration in seconds
            **process_config (dict): the process config kwargs specific to the simulator process

        Returns:
            ODEProcess instance
    """
    if not isinstance(entrypoint, str or dict[str, any]):
        raise ValueError('entrypoint must be a string sbml model path or a dict defining SED_MODEL within biosimulator_processes.data_model.sed_data_model')

    config = {'model': {'model_source': entrypoint, **process_config}} if isinstance(entrypoint, str) else entrypoint
    return ODEProcess(
        config={
            'process_address': f'local:{process_address}',
            'process_config': config,
            'observables': observables,
            'timestep': step_size,
            'runtime': duration
        },
        core=CORE)

