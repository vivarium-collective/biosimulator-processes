import os
from process_bigraph import Composite
from biosimulator_processes import CORE
from tests import ProcessUnitTest


def test_process():
    # 1. define the instance of the Composite(in this case singular) by its schema
    sbml_model_files_root = 'biosimulator_processes/model_files/sbml'
    model_name = 'vilar-discrete-SSA.xml'  # 'BIOMD0000000061_url.xml'
    model_fp = os.path.join(sbml_model_files_root, model_name)

    composite_document = {
        'tellurium': {
            '_type': 'step',
            'address': 'local:get_sbml',
            'config': {
                'biomodel_id': model_fp,
            },
            'inputs': {
                'time': ['start_time_store'],
                'run_time': ['run_time_store'],
                'floating_species': ['floating_species_store'],
                'boundary_species': ['boundary_species_store'],
                'model_parameters': ['model_parameters_store'],
                'reactions': ['reactions_store'],
                # 'interval': ['interval_store'],
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
                    'floating_species': 'tree[float]',
                    'time': 'float',
                },
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
                'time': ['start_time_store'],
            }
        }
    }

    # 2. make the composite
    workflow = Composite(
        config={'state': composite_document},
        core=CORE)

    # 3. run
    update = workflow.run(10)

    # 4. gather results
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')

    return ProcessUnitTest(instance_doc=instance)


if __name__ == '__main__':
    test_process()
