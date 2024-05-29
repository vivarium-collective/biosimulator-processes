"""As of 05/18/2024, most of the process implementations are considered Sed Processes"""

import os
import json

from process_bigraph import Composite, pp

from biosimulator_processes import CORE
from biosimulator_processes.helpers import prepare_single_ode_process_document
from biosimulator_processes.data_model.compare_data_model import ODECompositionResult


def test_ode_sed_processes(model_entrypoint: str, num_steps: int, duration: int = 1):
    # TODO: for now, just testing ode processes. Expand this *asap.
    local_ode_sed_process_addresses = ['tellurium', 'copasi', 'amici']
    return [
        ODECompositionResult(duration=duration, num_steps=num_steps, model_entrypoint=model_entrypoint, simulator_names=[sim_name])
        for sim_name in local_ode_sed_process_addresses]


def test_single_ode_sed_process(process_address: str, biomodel_id: str = None, model_fp: str = None):
    # biomodel_id = 'BIOMD0000000630'
    model_source = model_fp or biomodel_id
    assert model_source is not None, "You must provide either a biomodel id or an sbml model filepath"
    species_context = 'counts'
    species_port_name = f'floating_species_{species_context}'
    species_store = [f'floating_species_{species_context}_store']
    duration = 10

    assert os.path.exists(model_fp), "You must provide a valid sbml model file path"

    process_id = f'{model_fp.split("/")[-1] if model_fp else model_source}_test_process'
    instance = prepare_single_ode_process_document(
        simulator_name=process_address,
        process_id=process_id,
        sbml_model_fp=model_fp)

    composition = Composite(config={'state': instance}, core=CORE)
    composition.run(duration)
    return composition.gather_results()
