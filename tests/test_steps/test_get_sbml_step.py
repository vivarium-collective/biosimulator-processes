from biosimulator_processes.steps.get_sbml import GetSbml
from biosimulator_processes import CORE
from process_bigraph import pp, Composite


def test_step():
    biomodel_id = 'BIOMD0000000744'
    config = {'biomodel_id', biomodel_id}
    instance = {
        'get_sbml': {
            '_type': 'step',
            'address': 'local:get_sbml',
            'config': {
                'biomodel_id': biomodel_id,
            },
            'inputs': {
                'biomodel_id': ['biomodel_id_store']
            },
            'outputs': {
                'sbml_model_fp': ['sbml_model_fp_store'],
            }
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    'sbml_model_fp': 'string'
                },
            },
            'inputs': {
                'sbml_model_fp': ['sbml_model_fp_store'],
            }
        }
    }
    step_workflow = Composite(config={'state': instance}, core=CORE)
    step_workflow.run(1)
    result = step_workflow.gather_results()
    print(result)



test_step()
