import json
import os

from process_bigraph import pp

from verify_api.src.comparison import generate_ode_comparison


def test_step():
    biomodel_id = 'BIOMD0000000630'
    duration = 30
    n_steps = 42
    simulators = ['copasi', 'tellurium']

    results = generate_ode_comparison(biomodel_id, duration)
    results_fp = os.path.join(os.getcwd(), 'data', 'test_ode_comparator_step_result.txt')

    pp(f'The final results:\n{results}')

    with open(results_fp.replace('.txt', '.json'), 'w') as f:
        json.dump(results, f, indent=4)

    return results


if __name__ == '__main__':
    test_step()
