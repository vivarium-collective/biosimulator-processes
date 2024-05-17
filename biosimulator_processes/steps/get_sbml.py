from tempfile import mkdtemp
import os
import requests

import libsbml
from process_bigraph import Step, pp

from biosimulator_processes import CORE
from biosimulator_processes.io import fetch_sbml_file


class GetSbmlStep(Step):
    config_schema = {
        'biomodel_id': 'string',
        'save_dir': 'maybe[string]'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.biomodel_id = self.config['biomodel_id']
        self.save_dir = self.config.get('save_dir')

    def initial_state(self):
        return {'biomodel_id': self.config['biomodel_id']}

    def inputs(self):
        return {'biomodel_id': 'string'}

    def outputs(self):
        return {'sbml_model_fp': 'string'}

    def update(self, state):
        # TODO: Use copasi for this
        try:
            model_fp = fetch_sbml_file(biomodel_id=self.biomodel_id, save_dir=self.save_dir)
            return {'sbml_model_fp': model_fp}
        except Exception as e:
            print(e)
