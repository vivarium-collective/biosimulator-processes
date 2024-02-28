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
    # TODO: make this generalizable for those other than basico
    sbml = biomodels.get_content_for_model(model_id)
    return load_model_from_string(sbml)


def play_composition(instance: dict, duration: int):
    """Configure and run a Composite workflow."""
    workflow = Composite({
        'state': instance
    })
    workflow.run(duration)
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')
    return results


def generate_copasi_process_emitter_schema():
    return generate_emitter_schema(
        emitter_address='local',
        emitter_type='ram-emitter',
        floating_species='tree[float]',
        time='float'
    )


def generate_composite_copasi_process_instance(instance_name: str, config: Dict, add_emitter: bool = True) -> Dict:
    """Generate an instance of a single copasi process which is named `instance_name`
        and configured by `config` formatted to the process bigraph Composite API.

        Args:
            instance_name:`str`: name of the new instance referenced by PBG.
            config:`Dict`: see `biosimulator_processes.processes.copasi_process.CopasiProcess`
            add_emitter:`bool`: Adds emitter schema configured for CopasiProcess IO store if `True`. Defaults
                to `True`.
    """
    instance = {}
    instance[instance_name] = {
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
    }
    if add_emitter:
        instance['emitter'] = generate_copasi_process_emitter_schema()

    return instance


def generate_single_process_instance(
        instance_name: str,
        instance_config: dict,
        inputs_config: dict,
        outputs_config: dict,
        instance_type: str = 'step',
        instance_address: str = 'local:copasi',
) -> dict:
    return {
        instance_name: {
            '_type': instance_type,
            'address': instance_address,
            'config': instance_config,
            'inputs': inputs_config,
            'outputs': outputs_config
        }
    }


def generate_emitter_schema(
        emitter_address: str = "local",
        emitter_type: str = "ram-emitter",
        **emit_values_schema
) -> Dict:
    return {
        '_type': 'step',
        'address': 'local:ram-emitter',
        'config': {
            'emit': {**emit_values_schema},
        },
        'inputs': {  # TODO: make this generalized
            'floating_species': ['floating_species_store'],
            'time': ['time_store'],
        }
    }


def generate_parameter_scan_instance(
        num_iterations: int,
        entry_config: Dict,
        modeler: str,
        add_emitter: bool = True,
        *parameters,
        **io_config
) -> Dict:
    """Generate a parameter scan instance configuration for a given process."""
    instance = {}
    for n in range(num_iterations):
        iteration_name = f'{modeler}_{n}'
        iteration_instance = generate_single_process_instance(
            instance_name=iteration_name,
            instance_config=entry_config,
            inputs_config=io_config['inputs'],
            outputs_config=io_config['outputs'])

        for instance_name, instance_schema in iteration_instance:
            instance[instance_name] = iteration_instance

    if add_emitter:
        instance['emitter'] = generate_emitter_schema(
            floating_species='tree[float]',
            time='float')

    return instance


def perturb_parameter(param: str, degree: float):
    pass
