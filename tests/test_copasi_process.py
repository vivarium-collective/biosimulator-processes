import os
import json
from tests import ProcessUnitTest
from biosimulator_processes.utils import prepare_single_copasi_process_composite_doc


def test_process():
    biomodel_id = 'BIOMD0000000630'
    model_fp = f'../biosimulator_processes/model_files/sbml/{biomodel_id}_url.xml'
    species_context = 'counts'
    species_port_name = f'floating_species_{species_context}'
    species_store = [f'floating_species_{species_context}_store']
    duration = 10

    document = prepare_single_copasi_process_composite_doc()

    instance = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model': {
                    'model_source': model_fp
                },
                'method': 'lsoda'
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                'reactions': ['reactions_store']
            },
            'outputs': {
                'floating_species': ['floating_species_store'],
                'time': ['time_store'],
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
                'time': ['time_store'],
            }
        }
    }

    return ProcessUnitTest(instance_doc=instance, duration=20)


def test_process_from_document():
    # read the document from local file:
    five_process_fp = 'composer-notebooks/out/five_process_composite.json'
    with open(five_process_fp, 'r') as fp:
        instance = json.load(fp)

    return ProcessUnitTest(instance, duration=10)


if __name__ == '__main__':
    test_process()
