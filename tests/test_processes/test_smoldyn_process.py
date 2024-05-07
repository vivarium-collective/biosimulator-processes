import os
from tests import ProcessUnitTest


def test_process():
    smoldyn_models_root = 'biosimulator_processes/model_files/smoldyn'
    model_name = 'minE_model.txt'
    model_fp = os.path.join(smoldyn_models_root, model_name)

    instance = {
        'smoldyn': {
            '_type': 'process',
            'address': 'local:smoldyn',
            'config': {
                'model_filepath': model_fp,
            },
            'inputs': {
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store']},
            'outputs': {
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store']}
        },
        # 'emitter': {
        #     '_type': 'step',
        #     'address': 'local:ram-emitter',
        #     'config': {
        #         'emit': {
        #             'species_counts': 'tree[float]',
        #             'molecules': 'tree[float]',
        #         },
        #     },
        #     'inputs': {
        #         'floating_species': ['species_counts_store'],
        #         'molecules': ['molecules_store'],
        #     }
        # }
    }

    return ProcessUnitTest(instance_doc=instance, duration=10)


test_process()
