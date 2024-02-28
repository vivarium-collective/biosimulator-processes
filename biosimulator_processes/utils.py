from typing import Dict
from basico import biomodels, load_model_from_string
from process_bigraph import Composite, pf


def fetch_biomodel_by_term(term: str, index: int = 0):
    """Search for models matching the term and return an instantiated model from BioModels.

        Args:
            term:`str`: search term
            index:`int`: selector index for model choice

        Returns:
            `CDataModel` instance of loaded model.
        TODO: Implement a dynamic search of this
    """
    models = biomodels.search_for_model(term)
    model = models[index]
    return fetch_biomodel(model['id'])


def fetch_biomodel(model_id: str):
    # TODO: make this generalizable
    sbml = biomodels.get_content_for_model(model_id)
    return load_model_from_string(sbml)


def play_composition(instance: dict, duration: int):
    """Configure and run a Composite workflow"""
    workflow = Composite({
        'state': instance
    })
    workflow.run(duration)
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')
    return results


def generate_copasi_process_instance(instance_name: str, config: Dict) -> Dict:
    """Generate an instance of a single copasi process which is named `instance_name`
        and configured by `config` formatted to the process bigraph Composite API.

        Args:
            instance_name:`str`: name of the new instance referenced by PBG.
            config:`Dict`: see `biosimulator_processes.processes.copasi_process.CopasiProcess`
    """
    return {
        instance_name: {
            '_type': 'process',
            'address': 'local:copasi',
            'config': config,
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



