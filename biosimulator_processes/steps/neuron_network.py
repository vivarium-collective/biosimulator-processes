import os
from tempfile import mkdtemp

import numpy as np
from process_bigraph import Step
from pyneuroml import pynml
from pyneuroml.lems import LEMSSimulation
from neuroml.utils import validate_neuroml2

from biosimulator_processes import CORE
from biosimulator_processes.neuroml_functions import *


class SimpleNeuron(Step):
    config_schema = {
        'doc_config': {
            'doc_id': 'string',
            'model_name': 'string',
            'model_id': 'string',
            'param_config': 'tree[string]',  # these should be model-specific params as per neuroml
            'network_id': 'string'
        },
        'simulation_config': 'tree',  # defining simulation_id[str], duration[int], dt[float], simulation_seed[int], max_memory[str]
        'pulse_gen_config': {  # optional
            'amplitude': {
                '_type': 'string',
                '_default': "0.07 nA"
            },
            'delay': {
                '_type': 'string',
                '_default': "0ms"
            },
            'duration': {
                '_type': 'string',
                '_default': "1000ms"
            }
        },
        'save_dir': {  # optional
            '_type': 'string',
            '_default': mkdtemp()
        },
        'nml_filename': 'string'  # optional
    }

    def __init__(self, config, core=CORE):
        """Step implementation representing a single neuron model and simulation."""
        super().__init__(config, core)

        doc_config = self.config['doc_config']
        nml_doc = create_nml_doc(doc_config['doc_id'])
        model_id = doc_config['model_id']

        # define cell model instance
        self.cell_model = define_cell_model(
            nml_doc=nml_doc,
            cell_model_name=doc_config['model_name'],
            cell_model_id=model_id,
            **doc_config['param_config'])

        # define network instance
        self.network = create_network(
            nml_doc=nml_doc,
            network_id=doc_config.get('network_id', f'{model_id}_network'),
            validate=False)

        # create population for network in this case 1. TODO: dynamically add this based on config for n neurons
        self.population = create_population(network=self.network, pop_id=f'IzhPop0', cell_model=self.cell_model, size=1)

        # create the pulse generator which simulates and provides values for I
        pg_config = self.config['pulse_gen_config']
        pulse_generator, explicit_input = create_pulse_generator(
            nml_doc=nml_doc,
            network=self.network,
            gen_id=f'pulsegen_{model_id}',
            amplitude=pg_config['amplitude'],
            duration=pg_config['duration'],
            delay=pg_config['delay'],
            pop_id=self.population.id)

        # create the nml file to be used in update for the simulation
        save_dir = self.config['save_dir']
        # filename = self.config['nml_filename']
        # if not len(filename):
        self.nml_file = 'izhikevich2007_single_cell_network.nml'
        import neuroml.writers as writers
        writers.NeuroMLWriter.write(nml_doc, self.nml_file)

        # self.nml_file = write_neuroml_file(filename=filename, nml_doc=nml_doc, save_dir=save_dir)

        # get simulation config settings
        sim_config = self.config['simulation_config']
        self.simulation_id = sim_config['simulation_id']
        self.duration = sim_config.get('duration', 1000)  # TODO: make this default more relevant
        self.dt = sim_config.get('dt', 0.1)  # TODO: make this default scale automatically with duration
        self.simulation_seed = sim_config.get('simulation_seed', 123)
        self.max_sim_memory = sim_config.get('max_memory', "2G")
        self._results = {}

        try:
            validate_neuroml2(self.nml_file)
        except ValueError as ve:
            print(f'Your model could not be validated:\n{ve}')
            raise ve

    def initial_state(self):
        # TODO: possibly override the param config passed in constructor
        pass

    def inputs(self):
        # TODO: possibly override initial_state here
        pass

    def outputs(self):
        return {'duration': 'string', 'data': 'list'}

    def update(self, inputs):
        # TODO: perform the actual simulation here and return the values set in data_array
        dur = inputs.get('duration', self.duration)
        dt = inputs.get('dt', self.dt)
        seed = inputs.get('simulation_seed', self.simulation_seed)

        simulation_id = "example-single-izhikevich2007cell-sim"
        simulation = LEMSSimulation(sim_id=simulation_id,
                                    duration=1000, dt=0.1, simulation_seed=123)
        simulation.assign_simulation_target(self.network.id)
        simulation.include_neuroml2_file(self.nml_file)

        simulation.create_output_file(
            "output0",
            "%s.v.dat" % simulation_id)
        simulation.add_column_to_output_file("output0", 'IzhPop0[0]', 'IzhPop0[0]/v')

        lems_simulation_file = simulation.save_to_file()
        pynml.run_lems_with_jneuroml(
            lems_simulation_file,
            max_memory="2G",
            nogui=True,
            plot=False)

        data_array = np.loadtxt("%s.v.dat" % simulation_id)

        output = {
            'duration': dur,
            'data': data_array}

        self._results = output.copy()['data']

        return output

    def plot(self):
        return plot_recorded_data(data_array=self._results)




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

        self.network.validate()

        # create inter-population projection. TODO: enable iterative projection construction
        self.projections = []
        populations = list(self.populations.values())
        synapses = list(self.synapses.values())
        for i, population in enumerate(populations):
            if i < len(populations):
                pre_pop_id = populations[i]
                post_pop_id = populations[i + 1]

                proj = self.network.add(
                    "Projection",
                    id=f"proj_{i}",
                    presynaptic_population=pre_pop_id,
                    postsynaptic_population=post_pop_id,
                    synapse=synapses[i - 1]
                )
                self.projections.append(proj)
            else:
                pass
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
            'network': 'tree',
            'populations': 'tree',
            'projections': 'list'
        }

    def update(self, state):
        return {
            'synapses': self.synapses,
            'network': self.network,
            'populations': self.populations,
            'projections': self.projections
        }

