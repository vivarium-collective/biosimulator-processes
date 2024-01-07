from process_bigraph import Composite, pf


# def test_process():
#     instance = {
#         'fba': {
#             '_type': 'process',
#             'address': 'local:cobra',
#             'config': {
#                 'model_file': 'cobra_process/models/e_coli_core.xml'
#             },
#             'wires': {
#                 'fluxes': ['fluxes_store'],
#                 'objective_value': ['objective_value_store'],
#                 'reaction_bounds': ['reaction_bounds_store'],
#             }
#         },
#         'emitter': {
#             '_type': 'step',
#             'address': 'local:ram-emitter',
#             'config': {
#                 'ports': {
#                     'inputs': {
#                         'fluxes': 'tree[float]',
#                         'objective_value': 'tree[float]'
#                     }
#                 }
#             },
#             'wires': {
#                 'inputs': {
#                     'fluxes': ['fluxes_store'],
#                     'objective_value': ['objective_value_store']
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
#     # run
#     workflow.run(1)
#
#     # gather results
#     results = workflow.gather_results()
#     print(f'RESULTS: {pf(results)}')
