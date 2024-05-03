import os
import libsbml
import amici
from amici.sbml_import import get_species_initial
from tempfile import mkdtemp
from process_bigraph import Process
from biosimulator_processes import CORE
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE


class AmiciProcess(Process):
    config_schema = {
        'model': MODEL_TYPE,
        'species_context': {
            '_default': 'concentrations',
            '_type': 'string'
        }
        # TODO: add more amici-specific fields:: MODEL_TYPE should be enough to encompass this.
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        # TODO: Enable counts species_context

        # get and compile Amici model from SBML
        sbml_reader = libsbml.SBMLReader()
        sbml_doc = sbml_reader.readSBML(self.config['model']['model_source'])
        self.amici_model_object = sbml_doc.getModel()

        # set species context (concentrations for ODE by default)
        context_type = self.config['species_context']
        self.species_context_key = f'floating_species_{context_type}'
        self.use_counts = 'counts' in self.species_context_key

        # get species names
        self.species_objects = self.amici_model_object.getListOfSpecies()
        self.floating_species_list = [s.getId() for s in self.species_objects]
        self.floating_species_initial = [
            s.getInitialAmount() if self.use_counts else s.getInitialConcentration()
            for s in self.species_objects]

        # get model parameters
        model_parameter_objects = self.amici_model_object.getListOfParameters()
        self.model_parameters_list = [param.getName() for param in model_parameter_objects]
        self.model_parameters_values = [param.getValue() for param in model_parameter_objects]

        # get reactions
        reaction_objects = self.amici_model_object.reactions
        self.reaction_list = [reaction.getName() for reaction in reaction_objects]

        # get method
        self.method = self.amici_model_object.getSolver()

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

    def update(self, state, interval):
        # TODO: Complete this.`
        """COPIED FROM CopasiProcess:

                    for cat_id, value in inputs[self.species_context_key].items():
            set_type = 'particle_number' if 'counts' in self.species_context_key else 'concentration'
            species_config = {
                'name': cat_id,
                'model': self.copasi_model_object,
                set_type: value}
            set_species(**species_config)

        # run model for "interval" length; we only want the state at the end
        timecourse = run_time_course(
            start_time=inputs['time'],
            duration=interval,
            update_model=True,
            model=self.copasi_model_object,
            method=self.method)

        # extract end values of concentrations from the model and set them in results
        results = {'time': interval}
        for mol_id in self.floating_species_list:
            raw_mol_data = get_species(
                name=mol_id,
                exact=True,
                model=self.copasi_model_object)

            mol_data = raw_mol_data.particle_number[0] if self.use_counts else raw_mol_data.concentration[0]
            results[self.species_context_key] = {
                mol_id: float(mol_data)
            }
        """
        return {}
