"""
    Biosimulator process for Copasi/Basico.

    # 'model_file': 'string'
    # 'reactions': 'tree[string]',
    # 'model_changes': 'tree[string]',

    # Newton/Raphson method  distance/rate: steady state  Use newton method and time course simulation

    # try newton stopp if epsilon satisfies
    # run tc for 0.1unit of time stop if ep satis
    # try newton stop if e satisfied
    # run tc for 10x longer time stop if e
    # if time>10^10 units of time stop otherwise go back to number 3

"""


from typing import Dict, Union, Optional
from pandas import DataFrame
from basico import (
    load_model,
    get_species,
    get_parameters,
    get_reactions,
    set_species,
    run_time_course,
    get_compartments,
    new_model,
    set_reaction_parameters,
    add_reaction,
    set_reaction,
    set_parameters,
    add_parameter
)
from process_bigraph import Process, Composite, pf
from biosimulator_processes.utils import fetch_biomodel
from biosimulator_processes import CORE
from biosimulator_processes.data_model import MODEL_TYPE


class CopasiProcess(Process):
    """
        Entrypoints:

            A. SBML model file: 
            B. Reactions (name: {scheme: reaction contents(also defines species)) 'model'.get('model_changes')
            C. TimeCourseModel search term (load preconfigured model from BioModels)
    """

    config_schema = {
        'model': MODEL_TYPE,
        'method': {
            '_type': 'string',
            '_default': 'deterministic'
        }
    }

    def __init__(self,
                 config: Dict[str, Union[str, Dict[str, str], Dict[str, Optional[Dict[str, str]]], Optional[Dict[str, str]]]] = None,
                 core: Dict = None):
        super().__init__(config, core)

        # insert copasi process model config
        model_source = self.config['model']['model_source']['value']
        model_changes = self.config['model'].get('model_changes', {})
        self.model_changes = {} if model_changes is None else model_changes

        # A. enter with model_file
        if '/' in model_source:
            self.copasi_model_object = load_model(model_source)
        # B. enter with specific search term for a model
        elif 'BIO' in model_source:
            self.copasi_model_object = fetch_biomodel(model_id=model_source)
        # C. enter with a new model
        else:
            if not self.model_changes:
                raise AttributeError("You must pass a source of model changes specifying params, reactions, species or all three if starting from an empty model.")
            model_units = self.config['model'].get('model_units', {})
            self.copasi_model_object = new_model(
                name='CopasiProcess TimeCourseModel',
                **model_units)

        # ----REACTIONS: set reactions
        existing_reaction_names = get_reactions(model=self.copasi_model_object).index
        reaction_changes = self.model_changes.get('reaction_changes', [])
        if reaction_changes:
            for reaction_change in reaction_changes:
                reaction_name: str = reaction_change['reaction_name']
                param_changes: list[dict[str, float]] = reaction_change['parameter_changes']
                scheme_change: str = reaction_change.get('reaction_scheme')

                # handle changes to existing reactions
                if param_changes:
                    for param_name, param_change_val in param_changes:
                        set_reaction_parameters(param_name, value=param_change_val, model=self.copasi_model_object)
                if scheme_change:
                    set_reaction(name=reaction_name, scheme=scheme_change, model=self.copasi_model_object)
                # handle new reactions
                if reaction_name not in existing_reaction_names and scheme_change:
                    add_reaction(reaction_name, scheme_change, model=self.copasi_model_object)

        # Get a list of reactions
        self.reaction_list = get_reactions(model=self.copasi_model_object).index.tolist()
        if not self.reaction_list:
            raise AttributeError('No reactions could be parsed from this model. Your model must contain reactions to run.')

        # ----SPECS: set species changes
        species_changes = self.model_changes.get('species_changes', [])
        if species_changes:
            for species_change in species_changes:
                if isinstance(species_change, dict):
                    species_name = species_change.pop('name')
                    changes_to_apply = {}
                    for spec_param_type, spec_param_value in species_change.items():
                        if spec_param_value:
                            changes_to_apply[spec_param_type] = spec_param_value
                    set_species(**changes_to_apply, model=self.copasi_model_object)

        # Get the species (floating only)  TODO: add boundary species
        self.floating_species_list = get_species(model=self.copasi_model_object).index.tolist()
        self.floating_species_initial = get_species(model=self.copasi_model_object)['concentration'].tolist()

        # ----GLOBAL PARAMS: set global parameter changes
        global_parameter_changes = self.model_changes.get('global_parameter_changes', [])
        if global_parameter_changes:
            for param_change in global_parameter_changes:
                param_name = param_change.pop('name')
                for param_type, param_value in param_change.items():
                    if not param_value:
                        param_change.pop(param_type)
                    # handle changes to existing params
                    set_parameters(name=param_name, **param_change, model=self.copasi_model_object)
                    # set new params
                    global_params = get_parameters(model=self.copasi_model_object)
                    if global_params:
                        existing_global_parameters = global_params.index
                        if param_name not in existing_global_parameters:
                            assert param_change.get('initial_concentration') is not None, "You must pass an initial_concentration value if adding a new global parameter."
                            add_parameter(name=param_name, **param_change, model=self.copasi_model_object)

        # Get the list of parameters and their values (it is possible to run a model without any parameters)
        model_parameters = get_parameters(model=self.copasi_model_object)
        if isinstance(model_parameters, DataFrame):
            self.model_parameters_list = model_parameters.index.tolist()
            self.model_parameter_values = model_parameters['initial_value'].tolist()
        else:
            self.model_parameters_list = []
            self.model_parameter_values = []

        # Get a list of compartments
        self.compartments_list = get_compartments(model=self.copasi_model_object).index.tolist()

        # ----SOLVER: Get the solver (defaults to deterministic)
        self.method = self.config['method']

    def initial_state(self):
        floating_species_dict = dict(
            zip(self.floating_species_list, self.floating_species_initial))
        # keep in mind that a valid simulation may not have global parameters
        if self.model_parameters_list:
            model_parameters_dict = dict(
                zip(self.model_parameters_list, self.model_parameter_values))
        else:
            model_parameters_dict = {}
        return {
            'time': 0.0,
            'floating_species': floating_species_dict,
            'model_parameters': model_parameters_dict
        }

    def inputs(self):
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set',
            } for species_id in self.floating_species_list
        }
        if self.model_parameters_list:
            model_params_type = {
                param_id: 'float' for param_id in self.model_parameters_list
            }
        else:
            model_params_type = {}

        return {
            'time': 'float',
            'floating_species': floating_species_type,
            'model_parameters': model_params_type,
            'reactions': {
                reaction_id: 'float' for reaction_id in self.reaction_list},
        }

    def outputs(self):
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set',
            } for species_id in self.floating_species_list
        }
        return {
            'time': 'float',
            'floating_species': floating_species_type
        }

    def update(self, inputs, interval):
        # set copasi values according to what is passed in states
        for cat_id, value in inputs['floating_species'].items():
            set_species(
                name=cat_id,
                initial_concentration=value,
                model=self.copasi_model_object)

        # run model for "interval" length; we only want the state at the end
        timecourse = run_time_course(
            start_time=inputs['time'],
            duration=interval,
            update_model=True,
            model=self.copasi_model_object,
            method=self.method)

        # extract end values of concentrations from the model and set them in results
        results = {'time': interval}
        results['floating_species'] = {
            mol_id: float(get_species(
                name=mol_id,
                exact=True,
                model=self.copasi_model_object
            ).concentration[0])
            for mol_id in self.floating_species_list
        }
        return results


def test_process():
    CORE.process_registry.register('biosimulator_processes.processes.copasi_process.CopasiProcess', CopasiProcess)
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

    workflow = Composite(config={
        'state': instance  # initial_sim_state
    })
    workflow.run(10)
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')
