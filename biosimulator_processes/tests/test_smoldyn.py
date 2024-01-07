from process_bigraph import Composite, pf
# from biosimulator_processes.smoldyn_process import SmoldynProcess


def test_process():
    """Test the smoldyn process using the crowding model."""

    # this is the instance for the composite process to run
    instance = {
        'smoldyn': {
            '_type': 'process',
            'address': 'local:smoldyn_process',
            'config': {
                'model_filepath': 'biosimulator_processes/tests/model_files/minE_model.txt',
                'animate': False,
            },
            'wires': {  # this should return that which is in the schema
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store'],
            }
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'ports': {
                    'inputs': {
                        'species_counts': 'tree[any]',
                        'molecules': 'tree[any]'
                    },
                    'outputs': {
                        'species_counts': 'tree[any]',
                        'molecules': 'tree[any]'
                    },
                }
            },
            'wires': {
                'inputs': {
                    'species_counts': ['species_counts_store'],
                    'molecules': ['molecules_store'],
                }
            }
        }
    }

    # make the composite
    workflow = Composite({
        'state': instance
    })

    # run
    workflow.run(1)

    # gather results
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')


# def manually_test_process():
#     config = {
#         'model_filepath': 'biosimulator_processes/tests/model_files/minE_model.txt',
#         'animate': False
#     }
#     process = SmoldynProcess(config)
#     initial_state = process.initial_state()
#
#     stop = 1
#
#     result = test_smoldyn_manually(stop, process, historical=True)


# def test_smoldyn_manually(stop_time: int, process: SmoldynProcess, historical: bool = False):
#     current_state = process.initial_state()
#     runs = []
#     for t, _ in enumerate(list(range(stop_time)), 1):
#         result = process.update(current_state, t)
#         runs.append(result)
#         for species_id, delta in result['species_counts'].items():
#             current_state['species_counts'][species_id] += delta
#         if t == stop_time:
#             return result if not historical else runs
