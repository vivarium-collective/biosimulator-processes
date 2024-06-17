import random
import os
from tempfile import mkdtemp

import numpy as np
from neuroml.utils import component_factory
from pyneuroml import pynml
from neuroml import NeuroMLDocument
from pyneuroml.lems import LEMSSimulation
from neuroml.utils import component_factory
from neuroml.utils import validate_neuroml2
import neuroml.writers as writers
from process_bigraph import Process, Step

from biosimulator_processes import CORE


# -- MODEL CREATION --

def create_nml_doc(doc_id):
    return component_factory(NeuroMLDocument, id=doc_id)


def define_cell_model(nml_doc, cell_model_name: str, cell_model_id: str, **params):
    """Params should be specific to the cell model"""
    return nml_doc.add(cell_model_name, id=cell_model_id, **params)


def create_network(nml_doc, network_id: str, validate=False):
    return nml_doc.add("Network", id=network_id, validate=validate)


def create_population(network, size: int, pop_id: str, cell_model):
    return network.add("Population", id=pop_id, component=cell_model.id, size=size)


def _create_explicit_input(network, target_id: str, input_id: str):
    return network.add("ExplicitInput", target=target_id, input=input_id)


def create_pulse_generator(nml_doc, network, gen_id: str, delay: str, duration: str, amplitude: str, pop_id: str) -> tuple:
    # TODO: allow float parsing and auto formatting for string kwargs
    pg = nml_doc.add(
        "PulseGenerator",
        id=gen_id,
        delay=delay,
        duration=duration,
        amplitude=amplitude
    )

    exp_input = _create_explicit_input(network, target_id=pop_id, input_id=pg.id)
    return pg, exp_input


def write_neuroml_file(filename: str, nml_doc, save_dir: str = None) -> str:
    """Write a neuroml model to file and return the full save path of the file."""
    if not filename.endswith('.nml'):
        filename += '.nml'

    dest = os.path.join(save_dir, filename) if save_dir else filename
    try:
        writers.NeuroMLWriter.write(nml_doc, dest)
        print(f"Written network file to: {dest}")
        return dest
    except:
        return f"Could not write file to {dest}"


# -- MODEL SIMULATION --

def create_simulation(sim_id: str, duration: int, dt: float, network, nml_file: str, simulation_seed: int = 123) -> object:
    """Return a LEMS simulation object."""
    simulation = LEMSSimulation(sim_id=sim_id, duration=duration, dt=dt, simulation_seed=simulation_seed)
    simulation.assign_simulation_target(network.id)
    simulation.include_neuroml2_file(nml_file)
    return simulation


def generate_output_file(simulation: LEMSSimulation, sim_id: str, filename: str) -> str:
    """Save the output file and return its filepath."""
    simulation.create_output_file("output0", "%s.v.dat" % sim_id)
    simulation.add_column_to_output_file("output0", 'IzhPop0[0]', 'IzhPop0[0]/v')  # TODO: fix this.
    return simulation.save_to_file()


def run_simulation(sim_file: str, max_memory="2G", nogui=True, plot=False):
    """Run a LEMSSimulation file with the jNeuroML simulator."""
    return pynml.run_lems_with_jneuroml(sim_file, max_memory=max_memory, nogui=nogui, plot=plot)


def read_output_data(sim_id: str):
    return np.loadtxt("%s.v.dat" % sim_id)  # TODO: fix this.


# -- DATA ANALYSIS --

def plot_recorded_data(data_array, show_plot_already=True):
    return pynml.generate_plot(
        [data_array[:, 0]], [data_array[:, 1]],
        "Membrane potential", show_plot_already=True,
        xaxis="time (s)", yaxis="membrane potential (V)",
        save_figure_to="SingleNeuron.png"
    )


# -- STEP IMPLEMENTATIONS --

class SimpleNeuron(Step):
    config_schema = {
        'doc_config': {
            'doc_name': 'string',
            'doc_id': 'string',
            'model_name': 'string',
            'model_id': 'string',
            'param_config': 'tree[string]'
        },
        'save_dir': {
            '_type': 'string',
            '_default': mkdtemp()
        }
    }

    def __init__(self, config, core):
        """Step implementation representing a single neuron model and simulation."""
        super().__init__(config, core)



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

