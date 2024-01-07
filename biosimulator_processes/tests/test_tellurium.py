from process_bigraph import Composite, pf


def test_process():

    # this is the instance for the composite process to run...process instance keys may pertain to methods and not simulators directly
    instance = {
        'tellurium': {
            '_type': 'process',
            'address': 'local:tellurium_process',  # using a local toy process
            'config': {
                'sbml_model_path': 'biosimulator_processes/tests/model_files/BIOMD0000000061_url.xml',
            },
            'inputs': {
                'time': ['time_store'],
                'floating_species': ['floating_species_store'],
                'boundary_species': ['boundary_species_store'],
                'model_parameters': ['model_parameters_store'],
                'reactions': ['reactions_store'],
            },
            'outputs': {
                'reactions': ['reactions_store']
            }
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'ports': {
                    'inputs': {
                        'floating_species': 'tree[float]',
                    },
                    'outputs': {
                        'reactions': 'tree[float]'
                    }
                }
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
            },
            'outputs': {
                'reactions': ['reactions_store']
            }
        }
    }

    # make the composite
    workflow = Composite({
        'state': instance
    })

    # initial_state = workflow.initial_state()

    # run
    workflow.run(10)

    # gather results
    results = workflow.gather_results()
    print(f'RESULTS: {results}')


# def test_process_with_database_emitter():
#     # this is the instance for the composite process to run
#     instance = {
#         'tellurium': {
#             '_type': 'process',
#             'address': 'local:tellurium_process',  # using a local toy process
#             'config': {
#                 'sbml_model_path': 'biosimulator_processes/tests/model_files/BIOMD0000000061_url.xml',
#             },
#             'inputs': {
#                 'time': ['time_store'],
#                 'floating_species': ['floating_species_store'],
#                 'boundary_species': ['boundary_species_store'],
#                 'model_parameters': ['model_parameters_store'],
#                 'reactions': ['reactions_store'],
#             },
#             'outputs': {
#                 'reactions': ['reactions_store']
#             }
#         },
#         'emitter': {
#             '_type': 'step',
#             'address': 'local:database-emitter',
#             'config': {
#                 'ports': {
#                     'inputs': {
#                         'data': {
#                             'floating_species': 'tree[float]',
#                         },
#                         'experiment_id': 'string',
#                         'table': 'string',
#                         'floating_species': 'tree[float]',
#
#                     },
#                 }
#             },
#             'inputs': {
#                 'experiment_id': ['experiment_id_store'],
#                 'table': ['table_store'],
#                 'data': ['data_store', 'floating_species_store'],
#                 'floating_species': ['floating_species_store'],
#             }
#         }
#     }
#
#     # make the composite
#     workflow = Composite({
#         'state': instance
#     })
#
#     # initial_state = workflow.initial_state()
#
#     # run
#     workflow.run(10)
#
#     # gather results
#     results = workflow.gather_results()
#     print(f'RESULTS: {results}')


# def test_step():
#
#     # this is the instance for the composite process to run
#     instance = {
#         'start_time_store': 0,
#         'run_time_store': 1,
#         'results_store': None,  # TODO -- why is this not automatically added into the schema because of tellurium schema?
#         'tellurium': {
#             '_type': 'step',
#             'address': 'local:tellurium_step',  # using a local toy process
#             'config': {
#                 'sbml_model_path': 'biosimulator_processes/tests/model_files/BIOMD0000000061_url.xml',
#             },
#             'wires': {
#                 'inputs': {
#                     'time': ['start_time_store'],
#                     'run_time': ['run_time_store'],
#                     'floating_species': ['floating_species_store'],
#                     'boundary_species': ['boundary_species_store'],
#                     'model_parameters': ['model_parameters_store'],
#                     'reactions': ['reactions_store'],
#                 },
#                 'outputs': {
#                     'results': ['results_store'],
#                 }
#             }
#         }
#     }
#
#     # make the composite
#     workflow = Composite({
#         'state': instance
#     })
#
#     # initial_state = workflow.initial_state()
#
#     # run
#     update = workflow.run(10)
#
#     print(f'UPDATE: {update}')
#
#     # gather results
#     # results = workflow.gather_results()
#     # print(f'RESULTS: {pf(results)}')
