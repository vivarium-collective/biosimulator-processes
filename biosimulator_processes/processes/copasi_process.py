"""
    Biosimulator process for Copasi/Basico.

    # 'model_file': 'string'
    # 'reactions': 'tree[string]',
    # 'model_changes': 'tree[string]',

    # Newton/Raphson method  distance/rate: steady state  Use newton method and time course simulation

    # try newton stopp if epsilon satistfies
    # run tc for 0.1unit of time stop if ep satis
    # try newton stop if e satisfied
    # run tc for 10x longer time stop if e
    # if time>10^10 units of time stop otherwise go back to number 3

"""


from typing import Dict
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
    add_reaction,
    T,
    set_report_dict
)
from process_bigraph import Process, Composite, pf
from biosimulator_processes.utils import fetch_biomodel
from biosimulator_processes.data_model import Model, SedModel, MODEL_TYPE
import biosimulator_processes.processes


class CopasiProcess(Process):
    """
        Entrypoints:

            A. SBML model file: 
            B. Reactions (name: {scheme: reaction contents(also defines species)) 'model'.get('model_changes')
            C. Model search term (load preconfigured model from BioModels)

        Optional Parameters:

            A. 'model_changes', for example could be something like:
            
                    'model_changes': {
                        'species_changes': {   # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
                            'species_name': {
                                new_unit_for_species_name,
                                new_initial_concentration_for_species_name,
                                new_initial_particle_number_for_species_name,
                                new_initial_expression_for_species_name,
                                new_expression_for_species_name
                            }
                        },
                        'global_parameter_changes': {   # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
                            global_parameter_name: {
                                new_initial_value_for_global_parameter_name: 'any',
                                new_initial_expression_for_global_parameter_name: 'string',
                                new_expression_for_global_parameter_name: 'string',
                                new_status_for_global_parameter_name: 'string',
                                new_type_for_global_parameter_name: 'string'  # (fixed, assignment, reactions)
                            }
                        },
                        'reaction_changes': {
                            'reaction_name': {
                                'reaction_parameters': {
                                    reaction_parameter_name: 'float'  # (new reaction_parameter_name value)  <-- this is done with set_reaction_parameters(name="(REACTION_NAME).REACTION_NAME_PARAM", value=VALUE)
                                }, 
                                'reaction_scheme': 'string'   # <-- this is done like set_reaction(name = 'R1', scheme = 'S + E + F = ES')
                            }
                        }

                        
            B. 'method', changes the algorithm(s) used to solve the model
                COPASI support many different simulations methods:
                deterministic: using the COPASI LSODA implementation
                stochastic: using the Gibson Bruck algorithm
                directMethod: using the Gillespie direct method

            C. 'units', (tree): quantity, volume, time, area, length

        Justification:

            As per SEDML v4 specifications (section2.2.4), p.32:sed-ml-L1V4.

        MODEL_TYPE = {
            'model_id': 'string',    # could be used as the BioModels id
            'model_source': 'string',    # could be used as the "model_file" below (SEDML l1V4 uses URIs); what if it was 'model_source': 'sbml:model_filepath'  ?
            'model_language': {    # could be used to load a different model language supported by COPASI/basico
                '_type': 'string',
                '_default': 'sbml'    # perhaps concatenate this with 'model_source'.value? I.E: 'model_source': 'MODEL_LANGUAGE:MODEL_FILEPATH' <-- this would facilitate verifying correct model fp types.
            },
            'model_name': {
                '_type': 'string',
                '_default': 'composite_process_model'
            },
            'model_changes': {
                'species_changes': 'tree[string]',   # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
                'global_parameter_changes': 'tree[string]',  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
                'reaction_changes': 'tree[string]'
            }
        }
    """

    config_schema = {
        'model': MODEL_TYPE,
        'method': {
            '_type': 'string',
            '_default': 'deterministic'
        }
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)

        model_source = self.config['model']['model_source']['value']

        # A. enter with model_file
        if '/' in model_source:
            self.copasi_model_object = load_model(model_source)
        # B. enter with specific search term for a model
        elif 'BIO' in model_source:
            self.copasi_model_object = fetch_biomodel(model_id=model_source)
        # C. enter with a new model
        else:
            model_units = self.config['model'].get('model_units', {})
            self.copasi_model_object = new_model(
                name='CopasiProcess Model',
                **model_units)

        self.model_changes = self.config['model'].get('model_changes', {})

        # add reactions
        reaction_changes: Dict = self.model_changes.get('reaction_changes', None)
        if reaction_changes is not None:
            for reaction in reaction_changes:
                for reaction_name, reaction_scheme in reaction.items():
                    add_reaction(reaction_name, reaction_scheme, model=self.copasi_model_object)

        species_changes = self.model_changes.get('species_changes', None)
        if species_changes is not None:
            if isinstance(species_changes, dict):
                print(f'THE CHANGES: {species_changes}')
                for param_name, change in species_changes.items():
                    pass
                    # if not change:
                        # species_changes.pop(param_name)
                # set_species(**species_changes, model=self.copasi_model_object)
            elif isinstance(species_changes, list):
                for species_change in species_changes:
                    set_species(**species_change, model=self.copasi_model_object)

        # Get the species (floating only)  TODO: add boundary species
        self.floating_species_list = get_species(model=self.copasi_model_object).index.tolist()
        self.floating_species_initial = get_species(model=self.copasi_model_object)['concentration'].tolist()

        # Get the list of parameters and their values (it is possible to run a model without any parameters)
        model_parameters = get_parameters(model=self.copasi_model_object)
        if isinstance(model_parameters, DataFrame):
            self.model_parameters_list = model_parameters.index.tolist()
            self.model_parameter_values = model_parameters['initial_value'].tolist()
        else:
            self.model_parameters_list = []
            self.model_parameter_values = []

        # Get a list of reactions
        self.reaction_list = get_reactions(model=self.copasi_model_object).index.tolist()
        if not self.reaction_list:
            raise AttributeError('No reactions could be parsed from this model. Your model must contain reactions to run.')

        # Get a list of compartments
        self.compartments_list = get_compartments(model=self.copasi_model_object).index.tolist()

        self.method = self.config.get('method')
        # set_report_dict('Time-Course', task=T.TIME_COURSE, model=self.copasi_model_object, body=['Time'])

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
    initial_sim_state = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model_file': 'biosimulator_processes/model_files/Caravagna2010.xml'
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

    instance = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model': {
                    'model_source': 'biosimulator_processes/model_files/Caravagna2010.xml'
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

    workflow = Composite({
        'state': instance  # initial_sim_state
    })
    workflow.run(10)
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')
    assert ('emitter',) in results.keys(), "This instance was not properly configured with an emitter."


# if __name__ == "__main__":
#    test_process()
