import os
import logging
from tempfile import mkdtemp

import libsbml
import numpy as np
from amici import amici, SbmlImporter, import_model_module, Model, runAmiciSimulation
from amici.sbml_import import get_species_initial
from process_bigraph import Process

from biosimulator_processes import CORE
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulator_processes.utils import calc_duration, calc_num_steps, calc_step_size


class AmiciProcess(Process):
    """
       Parameters:
            config:`Dict`: dict keys include:
                model: SED Model Spec.
                species_context: Context by which to measure species outputs (defaults to concentrations).
                model_output_dir: Dirpath in which to save the AMICI model output.
                observables: for example:
                    observables = {
                        "observable_x1": {"name": "", "formula": "x1"},
                        "observable_x2": {"name": "", "formula": "x2"},
                        "observable_x3": {"name": "", "formula": "x3"},
                        "observable_x1_scaled": {"name": "", "formula": "scaling_x1 * x1"},
                        "observable_x2_offsetted": {"name": "", "formula": "offset_x2 + x2"},
                        "observable_x1withsigma": {"name": "", "formula": "x1"},
                    }
                constant_parameters: for example:
                    constant_parameters = ["k0"]
                sigmas: for example:
                    sigmas = {"observable_x1withsigma": "observable_x1withsigma_sigma"}



    """
    config_schema = {
        # SED and ODE-specific types
        'model': MODEL_TYPE,
        'time_config': {
            '_type': 'tree[string]',
            '_default': {}
        },
        'species_context': {
            '_default': 'concentrations',
            '_type': 'string'
        },
        # AMICI-specific types
        'model_output_dir': {
            '_default': mkdtemp(),
            '_type': 'string'
        },
        'working_dir': {
            '_default': '',
            '_type': 'string'
        },
        'observables': 'maybe[tree[string]]',
        'constant_parameters': 'maybe[list[string]]',
        'sigmas': 'maybe[tree[string]]'
        # TODO: add more amici-specific fields:: MODEL_TYPE should be enough to encompass this.
    }

    def __init__(self,
                 config=None,
                 core=CORE,
                 time_config: dict = None,
                 model_source: str = None,
                 sed_model_config: dict = None):

        if not config and model_source:
            config = {'model': {'model_source': model_source}}
        elif sed_model_config and config is not None:
            config['model'] = sed_model_config
        elif os.path.isdir(config.get('model')['model_source']):
            config['model']['model_source'] = [[os.path.join(root, f) for f in files if f.endswith('.xml') and not f.lower().startswith('manifest')][0] for root, _, files in os.walk(config.get('model').get('model_source'))][0]

        if time_config and not len(config.get('time_config', {}).keys()):
            config['time_config'] = time_config

        super().__init__(config=config, core=core)

        # reference model source and assert filepath
        model_fp = self.config['model'].get('model_source')
        assert model_fp is not None and '/' in model_fp, 'You must pass a valid path to an SBML model file.'
        model_config = self.config['model']

        # get and compile libsbml model from fp
        sbml_reader = libsbml.SBMLReader()
        sbml_doc = sbml_reader.readSBML(model_fp)
        self.sbml_model_object: libsbml.Model = sbml_doc.getModel()

        # get model args from config
        model_id = self.config['model'].get('model_id', None) \
            or model_fp.split('/')[-1].replace('.', '_').split('_')[0]

        model_output_dir = self.config['model_output_dir']

        # compile sbml to amici
        sbml_importer = SbmlImporter(model_fp)
        sbml_importer.sbml2amici(
            model_name=model_id,
            output_dir=model_output_dir,
            verbose=logging.INFO,
            observables=self.config.get('observables'),
            constant_parameters=self.config.get('constant_parameters'),
            sigmas=self.config.get('sigmas'))
        model_module = import_model_module(model_id, model_output_dir)
        self.amici_model_object: amici.Model = model_module.getModel()

        # set species context (concentrations for ODE by default)
        context_type = self.config['species_context']
        self.species_context_key = f'floating_species_{context_type}'
        self.use_counts = 'counts' in self.species_context_key

        # get species names
        self.species_objects = self.sbml_model_object.getListOfSpecies()
        self.floating_species_list = list(self.amici_model_object.getStateNames())
        self.floating_species_initial = list(self.amici_model_object.getInitialStates())

        # get model parameters
        self.model_parameter_objects = self.sbml_model_object.getListOfParameters()
        self.model_parameters_list = [param.getName() for param in self.model_parameter_objects]
        self.model_parameters_values = [param.getValue() for param in self.model_parameter_objects]

        # get reactions
        self.reaction_objects = self.sbml_model_object.reactions
        self.reaction_list = [reaction.getName() for reaction in self.reaction_objects]

        # get method
        self.method = self.amici_model_object.getSolver()

        # set time config and model with time config
        utc_config = self.config.get('time_config')
        assert utc_config, \
            "For now you must manually pass time_config: {duration: , num_steps: , step_size: , } in the config."
        self.step_size = utc_config.get('step_size')
        self.duration = utc_config.get('duration')
        self.num_steps = utc_config.get('num_steps')

        if len(list(utc_config.keys())) < 3:
            self._set_time_params()

        self.t = np.linspace(0, self.duration, self.num_steps)
        self.amici_model_object.setTimepoints(self.t)

    def _set_time_params(self):
        if self.step_size and self.num_steps:
            self.duration = calc_duration(self.num_steps, self.step_size)
        elif self.step_size and self.duration:
            self.num_steps = calc_num_steps(self.duration, self.step_size)
        else:
            self.step_size = calc_step_size(self.duration, self.num_steps)

    def initial_state(self):
        floating_species_dict = dict(
            zip(self.floating_species_list, self.floating_species_initial))

        model_parameters_dict = dict(
            zip(self.model_parameters_list, self.model_parameters_values))
        return {
            'time': 0.0,
            'floating_species_concentrations': floating_species_dict,
            'model_parameters': model_parameters_dict}

    def inputs(self):
        # dependent on species context set in self.config
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set'}
            for species_id in self.floating_species_list
        }

        model_params_type = {
            param_id: {
                '_type': 'float',
                '_apply': 'set'}
            for param_id in self.model_parameters_list
        }

        reactions_type = {
            reaction_id: 'float'
            for reaction_id in self.reaction_list
        }

        return {
            'time': 'float',
            self.species_context_key: floating_species_type,
            'model_parameters': model_params_type,
            'reactions': reactions_type}

    def outputs(self):
        floating_species_type = {
            species_id: {
                '_type': 'float',
                '_apply': 'set'}
            for species_id in self.floating_species_list
        }
        return {
            'time': 'float',
            self.species_context_key: floating_species_type}

    def update(self, inputs, interval):
        set_values = []
        for species_id, value in inputs[self.species_context_key].items():
            set_values.append(value)
        self.amici_model_object.setInitialStates(set_values)

        result_data = runAmiciSimulation(solver=self.method, model=self.amici_model_object)
        floating_species_results = dict(zip(
            self.floating_species_list,
            list(map(lambda x: result_data.by_id(f'{x}'), self.floating_species_list))))

        return {
            'time': interval,
            'floating_species_concentrations': floating_species_results
        }
