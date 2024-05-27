'''TODO: Implement this in ODESimulation base class:

    @abc.abstractmethod
    def _set_model_changes(self, **changes):
        self._set_floating_species_changes(**changes)
        self._set_global_parameters_changes(**changes)
        self._set_reactions_changes(**changes)


    @abc.abstractmethod
    def _set_floating_species_changes(self):
        """Sim specific method for starting values relative to this property."""
        pass

    @abc.abstractmethod
    def _set_global_parameters_changes(self):
        """Sim specific method for starting values relative to this property."""
        pass

    @abc.abstractmethod
    def _set_reactions_changes(self):
        """Sim specific method for starting values relative to this property."""
        pass
'''


import abc
import logging
import os.path
from typing import *

import tellurium as te
import numpy as np
from process_bigraph import Step
from process_bigraph.experiments.parameter_scan import RunProcess
from amici import amici, sbml_import, SbmlImporter
from COPASI import CDataModel
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

from biosimulator_processes import CORE
from biosimulator_processes.utils import calc_num_steps, calc_duration, calc_step_size
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulator_processes.io import parse_expected_timecourse_config, get_model_file_location, FilePath


class OdeSimulation(Step, abc.ABC):

    config_schema = {
        'model': MODEL_TYPE,  # model changes can go here. A dict of dicts of dicts: {'model_changes': {'floating_species': {'t': {'initial_concentration' value'}}}}
        'archive_filepath': 'maybe[string]',
        'time_config': {
            'duration': 'float',
            'num_steps': 'float',
            'step_size': 'float'
        }
    }

    def __init__(self,
                 archive_dirpath: str = None,
                 sbml_filepath: str = None,
                 time_config: Dict[str, Union[int, float]] = None,
                 config=None,
                 core=CORE):

        # verify entrypoints
        assert archive_dirpath or sbml_filepath and time_config or config, \
            "You must pass either an omex archive filepath, time config and sbml_filepath, or a config dict."

        utc_config = parse_expected_timecourse_config(archive_root=archive_dirpath) \
            if archive_dirpath else time_config

        assert len(list(utc_config.values())) >= 2, "you must pass two of either: step size, n steps, or duration."

        # parse config
        sbml_fp = sbml_filepath or get_model_file_location(archive_dirpath).path
        print(os.path.exists(sbml_fp))
        configuration = config or {'model': {'model_source': sbml_fp}, 'time_config': utc_config}

        # calc/set time params
        self.step_size = utc_config.get('step_size')
        self.num_steps = utc_config.get('num_steps')
        self.duration = utc_config.get('duration')
        if len(list(utc_config.values())) < 3:
            self._set_time_params()

        super().__init__(config=configuration, core=core)

        # set simulator library-specific attributes
        self.simulator = self._set_simulator(sbml_fp)
        self.floating_species_ids = self._get_floating_species_ids()
        self.t = np.linspace(0, self.duration, self.num_steps)

    def _set_time_params(self):
        if self.step_size and self.num_steps:
            self.duration = calc_duration(self.num_steps, self.step_size)
        elif self.step_size and self.duration:
            self.num_steps = calc_num_steps(self.duration, self.step_size)
        else:
            self.step_size = calc_step_size(self.duration, self.num_steps)

    @abc.abstractmethod
    def _set_simulator(self, sbml_fp: str) -> object:
        """Load simulator instance with self.config['sbml_filepath']"""
        pass

    @abc.abstractmethod
    def _get_floating_species_ids(self) -> list[str]:
        """Sim specific method"""
        pass

    def inputs(self):
        """For now, none"""
        return {}

    def outputs(self):
        return {
            'time': 'list[float]',
            'floating_species': {
                spec_id: 'float'
                for spec_id in self.floating_species_ids
            }
        }

    def update(self, inputs, **simulator_kwargs) -> Dict[str, Union[float, Dict[str, float]]]:
        """Iteratively update over self.floating_species_ids as per the requirements of the simulator library over
            this class' `t` attribute, which is are linearly spaced time-point vectors.
        """
        results = {
            'time': self.t,
            'floating_species': {
                mol_id: []
                for mol_id in self.floating_species_ids}}

        for i, ti in enumerate(self.t):
            start = self.t[i - 1] if ti > 0 else ti
            end = self.t[i]
            timecourse = self._run_simulation(
                start_time=start,
                duration=end,
                **simulator_kwargs)

            # TODO: just return the run time course return

            for mol_id in self.floating_species_ids:
                output = float(self._get_floating_species_concentrations(species_id=mol_id, model=self.simulator))
                results['floating_species'][mol_id].append(output)

        return results

    @abc.abstractmethod
    def _run_simulation(self, start_time, duration, **kwargs):
        """Run timecourse simulation as per simulator library requirements"""
        pass

    @abc.abstractmethod
    def _get_floating_species_concentrations(self, species_id: str, model: object = None):
        """Get floating species concentration values as per specific simulator library requirements"""
        pass


class CopasiStep(OdeSimulation):
    def __init__(self,
                 archive_dirpath: str = None,
                 sbml_filepath: str = None,
                 time_config: Dict[str, Union[int, float]] = None,
                 config=None,
                 core=CORE):
        super().__init__(archive_dirpath, sbml_filepath, time_config, config, core)

    def _set_simulator(self, sbml_fp: str) -> object:
        return load_model(sbml_fp)

    def _get_floating_species_ids(self) -> list[str]:
        species_data = get_species(model=self.simulator)
        assert species_data is not None, "Could not load species ids."
        return species_data.index.tolist()

    def outputs(self):
        return {
            'time': 'list[float]',
            'floating_species': {
                mol_id: 'list[float]'
                for mol_id in self.floating_species_ids
            }
        }

    """def update(self, inputs):
        results = {
            'time': self.t,
            'floating_species': {
                mol_id: []
                for mol_id in self.floating_species_ids}}

        for i, ti in enumerate(self.t):
            start = t[i - 1] if ti > 0 else ti
            end = t[i]
            timecourse = run_time_course(
                start_time=start,
                duration=end,
                step_number=1,
                # step_number=self.num_steps,
                update_model=True,
                model=self.simulator)

            # TODO: just return the run time course return

            for mol_id in self.floating_species_ids:
                output = float(
                    get_species(
                        name=mol_id,
                        exact=True,
                        model=self.simulator
                    ).concentration[0]
                )

                results['floating_species'][mol_id].append(output)

        return results"""

    def _run_simulation(self, start_time, duration, **kwargs):
        return run_time_course(
            start_time=start_time,
            duration=duration,
            update_model=True,
            model=self.simulator)

    def _get_floating_species_concentrations(self, species_id: str, model: object = None):
        return get_species(name=species_id, exact=True, model=self.simulator).concentration[0]


class TelluriumStep(OdeSimulation):
    def __init__(self,
                 archive_dirpath: str = None,
                 sbml_filepath: str = None,
                 time_config: Dict[str, Union[int, float]] = None,
                 config=None,
                 core=CORE):
        super().__init__(archive_dirpath, sbml_filepath, time_config, config, core)

    def _set_simulator(self, sbml_fp) -> object:
        return te.loadSBMLModel(sbml_fp)

    def _get_floating_species_ids(self) -> list[str]:
        return self.simulator.getFloatingSpeciesIds()

    def update(self, inputs):
        # run the simulation
        simulation_result = self.simulator.simulate(0, self.duration, self.num_steps)

        # extract the results and convert to update
        results = {'time': self.t}
        results['floating_species'] = {
            mol_id: float(self.simulator.getValue(mol_id))
            for mol_id in self.floating_species_list
        }

        return results


class AmiciStep(OdeSimulation):
    def __init__(self,
                 archive_dirpath: str = None,
                 sbml_filepath: str = None,
                 time_config: Dict[str, Union[int, float]] = None,
                 config=None,
                 core=CORE):
        super().__init__(archive_dirpath, sbml_filepath, time_config, config, core)
        self.simulator = self._set_simulator(sbml_filepath, model_dir)

    def _set_simulator(self, sbml_fp, model_dir) -> amici.Model:
        # get and compile libsbml model from fp
        sbml_reader = libsbml.SBMLReader()
        sbml_doc = sbml_reader.readSBML(model_fp)
        self.sbml_model_object: libsbml.Model = sbml_doc.getModel()

        # get model args from config
        model_id = self.config['model'].get('model_id', None) \
            or sbml_fp.split('/')[-1].replace('.', '_').split('_')[0]

        model_output_dir = model_dir

        # TODO: integrate # observables=self.config.get('observables'),
        #             # constant_parameters=self.config.get('constant_parameters'),
        #             # sigmas=self.config.get('sigmas'))

        # compile sbml to amici
        sbml_importer = SbmlImporter(sbml_fp)
        sbml_importer.sbml2amici(
            model_name=model_id,
            output_dir=model_output_dir,
            verbose=logging.INFO)
        model_module = import_model_module(model_id, model_output_dir)

        return model_module.getModel()

    def _get_floating_species_ids(self) -> list[str]:
        return self.simulator.getObservableIds()

    def update(self, inputs):
        results = {'time': self.t}
        results['floating_species'] = {
            mol_id: float(self.simulator.getValue(mol_id))
            for mol_id in self.floating_species_list
        }

        return results



class ODEProcess(RunProcess):
    def __init__(self,
                 address: str,
                 model_fp: str,
                 observables: list[list[str]],
                 step_size: float,
                 duration: float,
                 config=None,
                 core=CORE,
                 **kwargs):
        """
            Kwargs:
                'process_address': 'string',
                'process_config': 'tree[any]',
                'observables': 'list[path]',
                'timestep': 'float',
                'runtime': 'float'
        """
        configuration = config or {}
        if not config:
            configuration['process_address'] = address
            configuration['timestep'] = step_size
            configuration['runtime'] = duration
            configuration['process_config'] = {'model': {'model_source': model_fp}}
            configuration['observables'] = observables
        super().__init__(config=configuration, core=core)

    def run(self, inputs=None):
        input_state = inputs or {}
        return self.update(input_state)
