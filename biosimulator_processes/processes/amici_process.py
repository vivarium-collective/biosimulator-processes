import os
import amici
from tempfile import mkdtemp
from process_bigraph import Process
from biosimulator_processes import CORE
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE


class AmiciProcess(Process):
    config_schema = {
        'model': MODEL_TYPE,
        # TODO: add more amici-specific fields
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

        # get and compile Amici model from SBML
        sbml_importer = amici.SbmlImporter(self.config['model']['model_source'])
        model_name = self.config['model'].get('model_name', 'amici_process')
        model_dir = mkdtemp()
        sbml_importer.sbml2amici(model_name, model_dir)
        model_module = amici.import_model_module(model_name, model_dir)
        self.amici_model_object = model_module.getModel()

        # get method
        self.method = self.amici_model_object.getSolver()

    def initial_state(self):
        return {}

    def inputs(self):
        return {}

    def outputs(self):
        return {}

    def update(self, state, interval):
        return {}
