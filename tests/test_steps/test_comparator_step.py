import json
import os

from process_bigraph import pp

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


def test_step(verbose=False):
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
    obj = test_step(True)
    print(obj)
