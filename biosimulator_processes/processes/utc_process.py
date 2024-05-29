import os
import logging
from tempfile import mkdtemp
from abc import ABC, abstractmethod

import libsbml
import numpy as np
from process_bigraph import Process, Step

from biosimulator_processes import CORE
from biosimulator_processes.io import unpack_omex_archive, get_archive_model_filepath, get_sedml_time_config
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulator_processes.utils import calc_duration, calc_num_steps, calc_step_size


class UniformTimeCourse(Step):
    """ABC for UTC process declarations and simulations."""
    config_schema = {
        # SED and ODE-specific types
        'model': MODEL_TYPE,  # user may enter with one of sbml filepath, omex dirpath, or omex filepath in 'model_source'
        'time_config': {
            '_type': 'tree[string]',
            '_default': {}
        },
        'species_context': {
            '_default': 'concentrations',
            '_type': 'string'
        },
        'working_dir': {
            '_default': '',
            '_type': 'string'
        }
    }

    def __init__(self,
                 config=None,
                 core=CORE,
                 time_config: dict = None,
                 model_source: str = None,
                 sed_model_config: dict = None):

        # A. no config but either an omex file/dir or sbml file path
        configuration = config or {}
        if not configuration and model_source:
            configuration = {'model': {'model_source': model_source}}

        # B. has a config but wishes to override TODO: fix this.
        if sed_model_config and configuration:
            configuration['model'] = sed_model_config
        # C. has a config passed with an archive dirpath or filepath or sbml filepath as its model source:
        else:
            omex_path = configuration.get('model').get('model_source')
            # Ca: user has passed a dirpath of omex archive
            if os.path.isdir(omex_path) or omex_path.endswith('.omex'):
                if os.path.isdir(omex_path):
                    configuration['model']['model_source'] = get_archive_model_filepath(omex_path)
                    configuration['time_config'] = self._get_sedml_time_params(omex_path)
                # Cb: user has passed a zipped archive file
                elif omex_path.endswith('.omex'):  # TODO: fix this.
                    archive_dirpath = unpack_omex_archive(omex_path, working_dir=config.get('working_dir') or mkdtemp())
                    configuration['model']['model_source'] = get_archive_model_filepath(archive_dirpath)
                    configuration['time_config'] = self._get_sedml_time_params(archive_dirpath)

        if time_config and not len(configuration.get('time_config', {}).keys()):
            configuration['time_config'] = time_config

        super().__init__(config=configuration, core=core)

        # reference model source and assert filepath
        model_fp = self.config['model'].get('model_source')
        assert model_fp is not None and '/' in model_fp, 'You must pass a valid path to an SBML model file.'
        model_config = self.config['model']

        # set time config and model with time config
        utc_config = self.config.get('time_config')
        assert utc_config, \
            "For now you must manually pass time_config: {duration: , num_steps: , step_size: , } in the config."
        self.step_size = utc_config.get('step_size')
        self.duration = utc_config.get('duration')
        self.num_steps = utc_config.get('num_steps')
        self.output_start_time = utc_config.get('output_start_time') or 0
        self.species_context_key = 'floating_species_concentrations'

        if len(list(utc_config.keys())) < 3:
            self._set_time_params()

        self.floating_species_list = self._get_floating_species()
        self.model_parameters_list = self._get_model_parameters()
        self.reaction_list = self._get_reactions()
        self.t = np.linspace(self.output_start_time, self.duration, self.num_steps + 1)

    @staticmethod
    def _get_sedml_time_params(omex_path: str):
        sedml_fp = os.path.join(omex_path, 'simulation.sedml')
        sedml_utc_config = get_sedml_time_config(sedml_fp)
        output_end = int(sedml_utc_config['outputEndTime'])
        output_start = int(sedml_utc_config['outputStartTime'])
        duration = output_end - output_start
        n_steps = int(sedml_utc_config['numberOfPoints'])
        return {
            'duration': duration,
            'num_steps': n_steps,
            'step_size': calc_step_size(duration, n_steps),
            'output_start_time': output_start
        }

    def _set_time_params(self):
        if self.step_size and self.num_steps:
            self.duration = calc_duration(self.num_steps, self.step_size)
        elif self.step_size and self.duration:
            self.num_steps = calc_num_steps(self.duration, self.step_size)
        else:
            self.step_size = calc_step_size(self.duration, self.num_steps)

    def inputs(self):
        # dependent on species context set in self.config
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
            self.species_context_key: 'tree[string]',  # floating_species_type,
            'model_parameters': model_params_type,
            'reactions': reactions_type}

    def outputs(self):
        return {
            'time': 'float',
            self.species_context_key: 'tree[string]'}  # floating_species_type}

    @abstractmethod
    def _get_floating_species(self) -> list[str]:
        pass

    @abstractmethod
    def _get_model_parameters(self) -> list[str]:
        pass

    @abstractmethod
    def _get_reactions(self) -> list[str]:
        pass

    @abstractmethod
    def update(self, inputs=None):
        pass
