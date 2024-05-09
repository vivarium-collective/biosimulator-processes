from tempfile import mkdtemp
import os
import requests

import libsbml
from process_bigraph import Step, pp

from biosimulator_processes import CORE


class GetSbml(Step):
    config_schema = {
        'biomodel_id': 'string'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.biomodel_id = self.config['biomodel_id']

    def initial_state(self):
        return {'biomodel_id': self.config['biomodel_id']}

    def inputs(self):
        return {'biomodel_id': 'string'}

    def outputs(self):
        return {'sbml_model_fp': 'string'}

    def update(self, state):
        try:
            model_dirpath = os.getcwd()  # mkdtemp()
            biomodels_request_url = f'https://www.ebi.ac.uk/biomodels/search/download?models={self.biomodel_id}'
            response = requests.get(biomodels_request_url)
            response.raise_for_status()
            model_fp = os.path.join(model_dirpath, f'{self.biomodel_id}_url.xml')
            assert self.biomodel_id is not None
            with open(model_fp, 'wb') as f:
                f.write(response.content)

            print(model_fp)

            reader = libsbml.SBMLReader()
            document = reader.readSBML(model_fp)
            if document.getNumErrors() > 0:
                raise Exception('Error reading SBML file')

            model = document.getModel()
            if model is None:
                raise Exception('No model found in SBML file')
            else:
                print(f'{dir(model)}')

            return {'sbml_model_fp': model_fp}
        except Exception as e:
            print(e)
