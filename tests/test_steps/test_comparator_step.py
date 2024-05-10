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
    pp(f'Results for comparison test:\n{results}')

    results['verification_data'] = results[('verification_data',)]
    results.pop(('verification_data',))

    with open(os.path.join(os.getcwd(), 'comparator_result.txt'), 'w') as fp:
        fp.write(str(results))

    with open(os.path.join(os.getcwd(), 'comparator_result.json'), 'w') as f:
        json.dump(results, f, indent=4)

    return results


if __name__ == '__main__':
    test_step()
