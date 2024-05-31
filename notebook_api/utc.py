from typing import *

from biosimulator_processes.processes.amici_process import UtcAmici
from biosimulator_processes.processes.copasi_process import UtcCopasi
from biosimulator_processes.processes.tellurium_process import UtcTellurium
from biosimulator_processes.processes.utc_process import UniformTimeCourse


def generate_utc_step_outputs(omex_fp: str, simulators: list[str] = None) -> Dict[str, Union[List[UniformTimeCourse], Dict[str, List]]]:
    utc_simulators = ['AMICI', 'basiCO', 'Tellurium']
    simulators = simulators or utc_simulators
    instances = list(map(
        lambda utc_instance: utc_instance(config={'model': {'model_source': omex_fp}}),
        [UtcAmici, UtcCopasi, UtcTellurium]
    ))
    utc_output_data = list(map(
        lambda instance: instance.update(),
        instances
    ))
    results = dict(zip(list(map(lambda s: s.lower(), simulators)), utc_output_data))
    return {
        'results': results,
        'instances': instances
    }
