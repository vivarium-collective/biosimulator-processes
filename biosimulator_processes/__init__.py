import importlib
from typing import *

from builder import ProcessTypes
from bigraph_schema import TypeSystem
from process_bigraph import Composite

from biosimulator_processes.steps.viz import CompositionPlotter, Plotter2d
from biosimulator_processes.data_model.sed_data_model import MODEL_TYPE
from biosimulator_processes.utils import register_module


# Define a list of processes to attempt to import and register
PROCESSES_TO_REGISTER = [
    ('cobra', 'cobra_process.CobraProcess'),
    ('copasi', 'copasi_process.CopasiProcess'),
    ('smoldyn', 'smoldyn_process.SmoldynProcess'),
    ('tellurium', 'tellurium_process.TelluriumProcess'),
    ('amici', 'amici_process.AmiciProcess')]

STEPS_TO_REGISTER = [
    ('get_sbml', 'get_sbml.GetSbml'),
    ('plotter', 'viz.CompositionPlotter'),
    ('plotter2d', 'viz.Plotter2d')]

# core process registry implementation (unique to this package)
CORE = ProcessTypes()

# core type system implementation (unique to this package)
CORE.type_registry.register('sed_model', schema={'_type': MODEL_TYPE})
register_module(PROCESSES_TO_REGISTER, CORE)
register_module(STEPS_TO_REGISTER, CORE)
