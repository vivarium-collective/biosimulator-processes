from typing import Dict, Union, List, Tuple
from types import FunctionType
import os

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from basico import biomodels, load_model_from_string
from process_bigraph import Composite, pf, pp, ProcessTypes
import nbformat


def plot_utc_outputs(data: dict, t: Union[np.array, List[float]], simulator: str = None, x=None, y=None) -> None:
    """Plot ODE simulation observables with Seaborn."""
    plt.figure(figsize=(20, 8))
    species_data = data.get('floating_species') or data.get('floating_species_concentrations')
    for spec_name, spec_data in species_data.items():
        sns.lineplot(x=t, y=spec_data, label=spec_name)

    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title(f'Species Concentrations over Time with {simulator or "UTC Simulator"}')
    plt.legend()
    plt.grid(True)
    plt.show()


def plot_ode_output_data(data: dict, simulator_name: str, sample_size: int = None) -> None:
    """
    Args:
        data: outermost keys are 'time' and 'floating_species'

    Returns:

    """
    time: np.ndarray = data.get('results', data['time'])
    plt.figure(figsize=(20, 8))
    for name, output in data.get('floating_species', 'floating_species_concentrations').items():
        x = np.array(time)
        y = output
        plt.plot(x, y, label=name)

    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title(f'Species Concentrations Over Time with {simulator_name}')
    plt.legend()
    plt.grid(True)
    # plt.xlim([0, time[-1]])  # Set x-axis limits from 0 to the last time value
    # plt.ylim([min([list(v.values())[0] for v in spec_outputs]), max([list(v.values())[0] for v in spec_outputs])])  # Adjust y-axis to fit all data
    plt.show()


def create_ode_step_instance(simulator_name: str, **step_kwargs):
    module_name = 'ode_simulation'
    import_statement = 'biosimulator_processes.steps.ode_simulation'
    class_name = f'{simulator_name.replace(simulator_name[0], simulator_name[0].upper())}Step'
    module = __import__(
        import_statement, fromlist=[class_name])
    bigraph_class = getattr(module, class_name)
    return bigraph_class(**step_kwargs)


def calc_num_steps(dur, step_size) -> int:
    return int(dur / step_size)


def calc_duration(n_steps, step_size) -> int:
    return int(n_steps * step_size)


def calc_step_size(dur, n_steps) -> float:
    return dur / n_steps


def register_module(items_to_register: List[Tuple[str, str]], core: ProcessTypes, verbose=False) -> None:
    for process_name, path in items_to_register:
        module_name, class_name = path.rsplit('.', 1)
        try:
            library = 'steps' if 'process' not in path else 'processes'
            import_statement = f'biosimulator_processes.{library}.{module_name}'

            module = __import__(
                 import_statement, fromlist=[class_name])

            # module = importlib.import_module(import_statement)

            # Get the class from the module
            bigraph_class = getattr(module, class_name)

            # Register the process
            core.process_registry.register(process_name, bigraph_class)
        except ImportError as e:
            print(f"Cannot register {class_name}. Error:\n**\n{e}\n**")
            return
    print(f'Available processes:\n{pf(list(core.process_registry.registry.keys()))}') if verbose else None


def prepare_single_ode_process_document(
        process_id: str,
        simulator_name: str,
        sbml_model_fp: str,
        add_emitter=True
        ) -> Dict:
    """
        * `simulator_name` must correspond to an existing process implementation.
        # TODO: Make this more flexible by providing a default to biosimulators1.0 for tools not yet implemented.
    """
    species_context = 'concentrations'
    species_port_name = f'floating_species_{species_context}'
    species_store = [f'{process_id}_{species_port_name}_store']
    document = {
        process_id: {
            '_type': 'process',
            'address': f'local:{simulator_name}',
            'config': {
                'model': {
                    'model_source': sbml_model_fp}},
            'inputs': {
                species_port_name: species_store,
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                'reactions': ['reactions_store']},
            'outputs': {
                species_port_name: species_store,
                'time': ['time_store']}}}

    if add_emitter:
        document['emitter'] = {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    species_port_name: 'tree[float]',
                    'time': 'float'}},
            'inputs': {
                species_port_name: species_store,
                'time': ['time_store']}}

    return document


def prepare_single_copasi_process_schema(
        process_name: str,
        biomodel_id: str = None,
        sbml_model_fp: str = None,
        method='lsoda',
        species_context='concentrations',
        add_emitter=True
        ) -> Dict:
    species_port_name = f'floating_species_{species_context}'
    species_store = [f'floating_species_{species_context}_store']
    model_source = biomodel_id or sbml_model_fp
    assert model_source, 'You must pass either a biomodel id or sbml model path source.'
    document = {
        process_name: {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model': {
                    'model_source': model_source},
                'method': method,
                'species_context': species_context},
            'inputs': {
                species_port_name: species_store,
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                'reactions': ['reactions_store']},
            'outputs': {
                species_port_name: species_store,
                'time': ['time_store']}}}

    if add_emitter:
        document['emitter'] = {
            'emitter': {
                '_type': 'step',
                'address': 'local:ram-emitter',
                'config': {
                    'emit': {
                        species_port_name: 'tree[float]',
                        'time': 'float'}},
                'inputs': {
                    species_port_name: species_store,
                    'time': ['time_store']}}}

    return document


def run_composition(instance, duration: int = 10) -> dict:
    workflow = Composite(
        config={
            'state': instance
        }
    )
    workflow.run(duration)
    return workflow.gather_results()


def create_class_from_dict(instance_dict: Dict, class_name="DynamicClass"):
    """
    Dynamically create a class with attributes set to data based on the outermost keys of the given dictionary.
    """
    class_attrs = {key: val for key, val in instance_dict.items()}
    return type(class_name, (object,), class_attrs)


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


def generate_single_copasi_process_instance(instance_name: str, config: Dict, add_emitter: bool = True) -> Dict:
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
    """
        Args:
            **emit_values_schema:`kwargs`: values to be emitted by the address


    """
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


def generate_copasi_parameter_scan_instance(
        num_iterations: int,
        entry_config: Dict,
        # *parameters
):
    # TODO: select parameters
    parameter_scan_instance = {}
    origin_value = 3.00
    for n in range(num_iterations):
        iteration_model_config = generate_sed_model_config_schema(
            entrypoint={'biomodel_id': 'BIOMD0000000051'},
            species_changes={'Extracellular Glucose': {'initial_concentration': origin_value**n}},
            parameter_changes={'catp': {'initial_value': (origin_value - n)**n}}
        )
        iteration_instance = generate_single_copasi_process_instance(
            instance_name=f'copasi_{n}',
            config=iteration_model_config,
            add_emitter=False
        )
        for iter_name, iter_config in iteration_instance.items():
            parameter_scan_instance[iter_name] = iteration_instance

    emitter_schema = generate_emitter_schema(floating_species='tree[float]', time='float')
    parameter_scan_instance['emitter'] = emitter_schema

    return parameter_scan_instance



def generate_sed_model_config_schema(
        entrypoint: Dict,
        species_changes: Dict,
        parameter_changes: Dict,
        reaction_changes: Dict = None
) -> Dict:
    """
        Args:
            entrypoint:`Dict[str, str]`: per CopasiProcess config_schema; ie: {'biomodel_id': 'BIOMODEL>>>>'}
            species_changes:`Dict[str, Dict[str, any]]`: ie: {'a': {'initial_concentration': 32.3}}
            parameter_changes:`Dict[str, Dict[str, any]]`: ie: {'x2': {'expression': '1 -> A..'}}
            reaction_changes:`Dict[str, Union[str, Dict[str, Dict[str, any]]]`:
                    reaction_changes = {
                        'R1': {
                            'reaction_parameters': {
                                '(R1).k1': 23.2
                            },
                            'reaction_scheme': 'A -> B'
                        }

        Example:
            sed_model = sed_schema(
                entrypoint={'biomodel_id': 'BIOMD0000000051'},
                species_changes={'Extracellular Glucose': {'initial_concentration': 5.00}},
                parameter_changes={'catp': {'initial_value': 100.00}},
                reaction_changes={'Aldolase': {'scheme': 'A -> B'}}
            )
    """
    instance_schema = {
        'model': {
            'model_changes': {
                'species_changes': species_changes,
                'parameter_changes': parameter_changes,
                'reaction_changes': reaction_changes
            }
        }
    }

    for param_name, param_val in entrypoint.items():
        instance_schema['model'][param_name] = {
            param_name: param_val
        }

    return instance_schema


def perturb_parameter(num_iterations: int, degree: float):
    _range = []
    for n in range(num_iterations):
        if n > 0:
            n = n * degree
        _range.append(n)
    return _range


def perturb_parameter_numpy(num_iterations: int, degree: float):
    return np.linspace(start=0, stop=num_iterations, num=degree)


def fix_execution_count(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)

    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            if 'execution_count' not in cell:
                cell['execution_count'] = None
            print('execution_count' in cell)

    with open(notebook_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)


def fix_notebooks_execution_count():
    for root, _, files in os.walk('../composer-notebooks'):
        for _file in files:
            notebook_path = os.path.join(root, _file)
            fix_execution_count(notebook_path)


def get_copasi_parameter_type_default(
        getter: FunctionType,
        param_name: str,
        copasi_model_object: object,
        parameter_type: str
) -> Union[str, int, float]:
    """Return the default value of a given model parameter specified by `parameter_type`.

        Args:
            getter:`function`: basico callback with which to query the model. For example: `get_species`.
            param_name:`str`: parameter name to use as an argument in the `getter`. For example, if getter=get_species, this would be a species name.
            copasi_model_object:`CDataModel`: instance in memory which you are querying.
            parameter_type:`str`: which type of parameter you wish to get the default of based on the getter and param_name.

        For example:

                `get_copasi_parameter_type_default(get_species, 'T', p.copasi_model_object, 'unit')`
    """
    return getter(param_name, model=copasi_model_object)[[parameter_type]].values.tolist()[0][0]


def get_copasi_species_parameter_default(species_name: str, copasi_model_object: object, parameter_type: str):
    from basico import get_species
    return get_copasi_parameter_type_default(
        getter=get_species,
        param_name=species_name,
        copasi_model_object=copasi_model_object,
        parameter_type=parameter_type)
