import os
import warnings
from pathlib import Path
from types import FunctionType
from typing import *

import numpy as np
import cobra
from cobra.io import load_model, read_sbml_model
from basico import *
from process_bigraph import Process, Composite, ProcessTypes

from biosimulators_processes import CORE
from biosimulators_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulators_processes.simulator_functions import SIMULATOR_FUNCTIONS


class DynamicFBA(Process):
    config_schema = {
        'model': MODEL_TYPE,
        'simulator': 'string'
    }

    def __init__(self, config, core):
        super().__init__(config, core)
        model_file = self.config['model']['model_source']
        self.simulator = self.config['simulator']

        # create cobra model
        data_dir = Path(os.path.dirname(model_file))
        path = data_dir / model_file.split('/')[-1]
        self.cobra_model = read_sbml_model(str(path.resolve()))

    def initial_state(self):
        # 1. get initial species concentrations from simulator
        # 2. influence fba bounds with #1
        # 3. call cobra_model.optimize() and give vals
        pass

    def inputs(self):
        pass

    def outputs(self):
        return {'solution': 'tree[float]'}

    def update(self, state, interval):
        simulator_method: FunctionType = SIMULATOR_FUNCTIONS[self.simulator]


