import random
import os
from tempfile import mkdtemp

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
        'network_config': {
            'network_id': 'string',
            'validate': {
                '_type': 'boolean',
                '_default': False
            },
            'population_config': 'tree'  # {population_id: {size: 5, property_config: {tag: str, value: str} <-- optional}}
        },
        'save_dir': {
            '_type': 'string',
            '_default': mkdtemp()
        },
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
        self.model = nml_doc.add(model_name, id=model_id, **model_params_config)
        self.model.info(True)

        # create a synapse component and add it to the doc
        # TODO: parse number of neurons and (n) and create n - 1 synapses.
        self.synapses = {}
        for i, synapse_config in enumerate(self.config['synapse_config'].items()):
            self.synapses[f'synapse_{i}'] = self._create_synapse(
                nml_doc=nml_doc,
                name=synapse_config[0],
                synapse_id=synapse_config[1]['synapse_id'],
                **synapse_config[1]['synapse_params'])

        # create the network and add populations (neurons)
        net_config = self.config['network_config']
        self.network = nml_doc.add("Network", id=net_config['network_id'], validate=net_config['validate'])
        self.populations = {}
        for pop_id, pop_config in net_config['population_config'].items():
            population = self._create_population(population_id=pop_id, **pop_config)
            self.network.add(population)
            self.populations[population.id] = population

        # write-out nml file with validation
        save_dir = self.config.get('save_dir')
        self.nml_file = os.path.join(save_dir, f"{model_id}.nml")
        writers.NeuroMLWriter.write(nml_doc, self.nml_file)
        pynml.validate_neuroml2(self.nml_file)

    def _create_synapse(self, nml_doc: object, name: str, synapse_id: str, gbase: str, erev: str, tau_decay: str):
        return nml_doc.add(name, id=synapse_id, gbase=gbase, erev=erev, tau_decay=tau_decay)

    def _create_population(self, size: int, population_id: str, property_config: dict = None):
        population = component_factory(
            "Population",
            id=population_id,
            component=self.model.id,
            size=size)

        if property_config:
            population.add("Property", **property_config)

        # TODO: Add population projection with pulse generation here.
        return population

    def outputs(self):
        return {
            'synapses': 'tree',
            'network': 'tree'
        }

    def update(self, state):
        return {
            'synapses': self.synapses,
            'network': self.network
        }

