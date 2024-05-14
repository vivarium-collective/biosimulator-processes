import json
import os

from process_bigraph import pp, pf

from biosimulator_processes.data_model import BaseModel
from biosimulator_processes.data_model.compare_data_model import ODEIntervalResult, ODEComparisonResult
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


def test_ode_comparison_result():
    dur = 30
    n_steps = 300
    biomodel_id = 'BIOMD0000000630'
    ode_comparison_result = ODEComparisonResult(duration=dur, num_steps=n_steps, biomodel_id=biomodel_id)
    pp(pf(ode_comparison_result.to_dict()))
    with open('/Users/alexanderpatrie/Desktop/repos/biosimulator-processes/test_outputs' + '/test_ode_comparison_object.json', 'w') as f:
        json.dump(ode_comparison_result.to_dict(), f, indent=4)


def test_step():
    biomodel_id = 'BIOMD0000000630'
    duration = 30
    n_steps = 42
    simulators = ['copasi', 'tellurium', 'amici']

    results_dict = generate_ode_comparison(biomodel_id, duration)
    results_fp = os.path.join(os.getcwd(), 'test_outputs', 'test_ode_comparator_step_result.txt')

    interval_results = generate_ode_interval_outputs(duration, n_steps, biomodel_id)

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
    test_ode_comparison_result()
