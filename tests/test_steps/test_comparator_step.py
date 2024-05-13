import json
import os

from process_bigraph import pp

from biosimulator_processes.data_model import BaseModel
from verify_api.src.comparison import generate_ode_comparison, generate_ode_comparison_result_object


"""
 "outputs": [
        {
            "copasi_simple_floating_species_concentrations": {
                "plasminogen": 0.0,
                "plasmin": 0.0,
                "single intact chain urokinase-type plasminogen activator": 0.0,
                "two-chain urokinase-type plasminogen activator": 0.0,
                "x": 0.0,
                "x-plasmin": 0.0
            },

"""


from typing import *


class ODEIntervalResult(BaseModel):
    interval_id: float
    copasi_floating_species_concentrations: Dict[str, float]
    tellurium_floating_species_concentrations: Dict[str, float]
    amici_floating_species_concentrations: Dict[str, float]
    time: float


def test_step():
    biomodel_id = 'BIOMD0000000630'
    duration = 30
    n_steps = 42
    simulators = ['copasi', 'tellurium', 'amici']

    results_dict = generate_ode_comparison(biomodel_id, duration)
    results_fp = os.path.join(os.getcwd(), 'test_outputs', 'test_ode_comparator_step_result.txt')

    interval_results = []
    simulator_names = ['copasi', 'tellurium', 'amici']
    for global_time_index, interval_result_data in enumerate(results_dict['outputs']):
        print(global_time_index)
        print(interval_result_data, interval_result_data.keys())

        interval_config = {}
        for k, v in interval_result_data.items():
            if 'species' in k:
                interval_config['copasi_floating_species_concentrations'] = v

        interval_result = ODEIntervalResult(
            interval_id=float(global_time_index),
            copasi_floating_species_concentrations=interval_result_data['copasi_floating_species_concentrations'],
            amici_floating_species_concentrations=interval_result_data['amici_floating_species_concentrations'],
            tellurium_floating_species_concentrations=interval_result_data['tellurium_floating_species_concentrations'],
        )


def test_step_object(verbose=False):
    biomodel_id = 'BIOMD0000000630'
    duration = 30
    n_steps = 42
    simulators = ['copasi', 'tellurium', 'amici']

    results_dict = generate_ode_comparison(biomodel_id, duration)
    results_fp = os.path.join(os.getcwd(), 'test_outputs', 'test_ode_comparator_step_result.txt')

    if verbose:
        pp(f'The final results:\n{results_dict}')

    comparison_result_obj = generate_ode_comparison_result_object(results_dict, duration, n_steps, simulators)
    with open(results_fp.replace('.txt', '.json'), 'w') as f:
        json.dump(comparison_result_obj.model_dump(), f, indent=4)

    return comparison_result_obj


if __name__ == '__main__':
    test_step()
