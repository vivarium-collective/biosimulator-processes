import abc
import logging
from typing import *

from process_bigraph import Step
from process_bigraph.experiments.parameter_scan import RunProcess
import tellurium as te
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


class OdeSimulation(Step, abc.ABC):

    config_schema = {
        'model': MODEL_TYPE,
        'time_config': {
            'step_size': 'maybe[float]',
            'num_steps': 'maybe[float]',
            'duration': 'maybe[float]'
        }
    }

    def __init__(self, sbml_filepath: str = None, time_config: dict[str, float] = None, config=None, core=CORE):
        assert sbml_filepath and time_config or config, "You must pass either a time config and sbml_filepath or a config dict."
        configuration = config or {
            'model': {
                'model_source': sbml_filepath
                # model changes can go here. A dict of dicts of dicts: {'model_changes': {'floating_species': {'t': {'initial_concentration' value'}}}}
            },
            'time_config': time_config
        }
        assert len(list(time_config.values())) >= 2, "you must pass two of either: step size, n steps, or duration."
        self.step_size = time_config.get('step_size')
        self.num_steps = time_config.get('num_steps')
        self.duration = time_config.get('duration')
        self._set_time_params()

        super().__init__(config=configuration, core=core)

        self.simulator = self._set_simulator(sbml_filepath)
        self.floating_species_ids = self._get_floating_species_ids()
        self.t = [float(n) for n in range(int(self.duration))]

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

    '''
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
        pass'''

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

    @abc.abstractmethod
    def update(self, inputs) -> Dict[str, Union[float, Dict[str, float]]]:
        """Iteratively update over self.floating_species_ids as per the requirements of the simulator library."""
        pass


class CopasiStep(OdeSimulation):
    def __init__(self, sbml_filepath, time_config: dict[str, float], config=None, core=CORE):
        super().__init__(sbml_filepath, time_config, config, core)
        # self.simulator = self._set_simulator(self.config['sbml_filepath'])
        # self.floating_species_ids = self._get_floating_species_ids()

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
            },
            'species_data': {
                mol_id: 'list[float]'
                for mol_id in self.floating_species_ids
            }
        }

    def update(self, inputs):
        results = {
            'time': self.t,
            'floating_species': {
                mol_id: []
                for mol_id in self.floating_species_ids
            },
            'species_data': {
                mol_id: []
                for mol_id in self.floating_species_ids
            }
        }
        i = 0.0
        for n in range(int(self.duration)):
            timecourse = run_time_course(
                start_time=i,
                duration=float(n),
                step_number=1,
                # step_number=self.num_steps,
                update_model=True,
                model=self.simulator)



            # TODO: just return the run time course

            for mol_id in self.floating_species_ids:
                output = float(get_species(
                    name=mol_id,
                    exact=True,
                    model=self.simulator).concentration[0])

                results['floating_species'][mol_id].append(output)
            i += 1

        return results


class TelluriumStep(OdeSimulation):
    def __init__(self, sbml_filepath, time_config: dict[str, float], config=None, core=CORE):
        super().__init__(sbml_filepath, time_config, config, core)
        # self.simulator = self._set_simulator(sbml_filepath)

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
    def __init__(self, sbml_filepath, time_config: dict[str, float], model_dir: str, config=None, core=CORE):
        super().__init__(sbml_filepath, time_config, config, core)
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
