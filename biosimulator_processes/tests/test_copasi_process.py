import os
import json
from process_bigraph import Composite, pf
from biosimulator_processes import CORE
from biosimulator_processes.tests import ProcessUnitTest


def test_process():
    sbml_model_files_root = 'biosimulator_processes/model_files/sbml'
    model_name = 'vilar-discrete-SSA.xml'  # 'BIOMD0000000061_url.xml'
    model_fp = os.path.join(sbml_model_files_root, model_name)

    biomodel_id = 'BIOMD0000000630'

    instance = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model': {
                    'model_source': biomodel_id  # model_fp
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
