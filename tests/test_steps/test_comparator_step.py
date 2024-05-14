import json
import os

from process_bigraph import pp, pf

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


class IntervalResult(BaseModel):
    interval_id: float


def generate_ode_interval_results(duration: int, n_steps: int, biomodel_id: str) -> List[IntervalResult]:
    class ODEIntervalResult(IntervalResult):
        interval_id: float
        copasi_floating_species_concentrations: Dict[str, float]
        tellurium_floating_species_concentrations: Dict[str, float]
        amici_floating_species_concentrations: Dict[str, float]
        time: float

    def _generate_ode_interval_results(duration: int, n_steps: int, biomodel_id: str) -> List[ODEIntervalResult]:
        results_dict = generate_ode_comparison(biomodel_id, duration)
        simulator_names = ['copasi', 'tellurium', 'amici']
        interval_results = []

        for global_time_index, interval_result_data in enumerate(results_dict['outputs']):
            interval_config = {
                'interval_id': float(global_time_index),
                'time': interval_result_data['time']
            }

            for k, v in interval_result_data.items():
                for simulator_name in simulator_names:
                    if simulator_name in k:
                        interval_config[f'{simulator_name}_floating_species_concentrations'] = v

            interval_result = ODEIntervalResult(**interval_config)
            interval_results.append(interval_result)

        return interval_results

    return _generate_ode_interval_results(duration, n_steps, biomodel_id)


def test_step():
    biomodel_id = 'BIOMD0000000630'
    duration = 30
    n_steps = 42
    simulators = ['copasi', 'tellurium', 'amici']

    results_dict = generate_ode_comparison(biomodel_id, duration)
    results_fp = os.path.join(os.getcwd(), 'test_outputs', 'test_ode_comparator_step_result.txt')

    interval_results = generate_ode_interval_results(duration, n_steps, biomodel_id)

    outs = ''
    for i, v in enumerate(interval_results):
        print(i)
        pp(v)
        outs += f'{i}\n{pf(v)}\n\n'

    with open('/Users/alexanderpatrie/Desktop/repos/biosimulator-processes/test_outputs' + '/test_ode_comparator_step_result.txt', 'w') as f:
        f.write(outs)
        f.close()




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
