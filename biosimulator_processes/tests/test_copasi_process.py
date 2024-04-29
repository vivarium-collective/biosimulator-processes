import os
import json 
from process_bigraph import pp, Composite
# from biosimulator_processes.tests.data_model import ProcessUnitTest


def test():
    # model_fp = 'biosimulator_processes/model_files/Caravagna2010.xml'
    model_fp = 'biosimulator_processes/model_files/BIOMD0000000061_url.xml'

    instance = {
        'copasi': {
            '_type': 'process',
            'address': 'local:!biosimulator_processes.processes.copasi_process.CopasiProcess',
            'config': {
                'model': {
                    'model_source': model_fp  # {
                    #     'value': 'biosimulator_processes/model_files/Caravagna2010.xml'}
                },
                'method': 'directMethod'  # 'stochastic'
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
    # return ProcessUnitTest(instance, write_results=True, out_dir=os.getcwd())

    workflow = Composite(config={
        'state': instance
    })
    workflow.run(10)
    results = workflow.gather_results()
    print(f'\nTHE RESULTS: {results}')


"""def test_process_from_document(input_fp: str):
    # read the document from local file:
    '''root_fp = os.path.abspath('../..')
    five_process_fp = os.path.join(root_fp, 'notebooks/out/five_process_composite.json')
    with open(five_process_fp, 'r') as fp:
        instance = json.load(fp)'''

    with open(input_fp, 'r') as fp:
        instance = json.load(fp)

    # results = run_composition(instance, 10)
    print(f'Results:')
    # pp(results)


    
def test_process_from_document():
    import json
    # ensure that the process is registered
    # CORE.process_registry.register('biosimulator_processes.processes.copasi_process.CopasiProcess', CopasiProcess)

    # read the document from local file:
    five_process_fp = '../../notebooks/out/five_process_composite.json'
    # with open(five_process_fp, 'r') as fp:
    #     instance = json.load(fp)
    # workflow = Composite(config={
    #     'state': instance
    # })
    print(os.path.exists(five_process_fp))
    print(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
"""


'''def test_process():
    instance = {
        'copasi': {
            '_type': 'process',
            'address': 'local:!biosimulator_processes.processes.copasi_process.CopasiProcess',
            'config': {
                'model': {
                    'model_source': {
                        'value': 'biosimulator_processes/model_files/Caravagna2010.xml'}
                }
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

    results = run_composition(instance, 10)
    print(f'Results:')
    pp(results)'''

if __name__ == '__main__':
    test()
