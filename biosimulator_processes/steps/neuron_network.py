import random

import numpy as np
from neuroml.utils import component_factory
from pyneuroml import pynml
from pyneuroml.lems import LEMSSimulation
import neuroml.writers as writers
from process_bigraph import Process, Step

from biosimulator_processes import CORE


class SimpleNeuronNetwork(Step):
    config_schema = {
        'num_neurons': 'integer',
        'doc_config': {
            'doc_name': 'string',
            'doc_id': 'string',
            'model_name': 'string',
            'model_id': 'string',
            'param_config': 'tree[string]'
        },
        'synapse_config': 'tree[string]',  # {'synapse_name': {synapse_id: '', synapse_params: {}}}
        # 'network_config': {
        #     'network_id': 'string',
        #     'validate': {
        #         '_type': 'boolean',
        #         '_default': False
        #     },
        #     'num_population': 'integer',
        #     'population_config': 'tree'  # indexted by population: population size, etc
        # }
    }

    def __init__(self, config, core=CORE):
        super().__init__(config, core)

        num_neurons = self.config['num_neurons']
        num_synapses = num_neurons - 1

        # declare and configure the entire model
        model_config = self.config.get('doc_config')
        doc_name = model_config['doc_name']
        doc_id = model_config['doc_id']

        model_name = model_config['model_name']  # ie: Cell id like "Izhikevich2007Cell"
        model_id = model_config['model_id']
        model_params_config = model_config['param_config']

        # create the doc container
        nml_doc = component_factory(doc_name, id=doc_id)

        # add model-specific param state to doc
        model = nml_doc.add(model_name, id=model_id, **model_params_config)
        model.info(True)

        # create a synapse component and add it to the doc
        # TODO: parse number of neurons and (n) and create n - 1 synapses.

        self.synapses = {}
        for i, synapse_config in enumerate(self.config['synapse_config'].items()):
            self.synapses[f'synapse_{i}'] = self._create_synapse(
                nml_doc=nml_doc,
                name=synapse_config[0],
                synapse_id=synapse_config[1]['synapse_id'],
                **synapse_config[1]['synapse_params'])

    def _create_synapse(self, nml_doc: object, name: str, synapse_id: str, gbase: str, erev: str, tau_decay: str):
        return nml_doc.add(name, id=synapse_id, gbase=gbase, erev=erev, tau_decay=tau_decay)

    def outputs(self):
        return {
            'synapses': 'tree'
        }

    def update(self, state):
        return {
            'synapses': self.synapses
        }

