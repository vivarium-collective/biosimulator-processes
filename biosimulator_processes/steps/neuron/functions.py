import random
import os

import numpy as np
from neuroml.utils import component_factory
from pyneuroml import pynml
from neuroml import NeuroMLDocument
from pyneuroml.lems import LEMSSimulation
from neuroml.utils import component_factory
from neuroml.utils import validate_neuroml2
import neuroml.writers as writers


__all__ = [
    'create_network',
    'create_nml_doc',
    'define_cell_model',
    'create_population',
    'create_pulse_generator',
    'write_neuroml_file',
    'create_simulation',
    'generate_output_file',
    'run_simulation',
    'read_output_data',
    'plot_recorded_data'
]


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
