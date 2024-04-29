import importlib

from builder import ProcessTypes
from process_bigraph import Composite

from biosimulator_processes.data_model import SedDataModel


# Define a list of processes to attempt to import and register
PROCESSES_TO_REGISTER = [
    ('cobra', 'cobra_process.CobraProcess'),
    ('copasi', 'copasi_process.CopasiProcess'),
    ('smoldyn', 'smoldyn_process.SmoldynProcess'),
    ('tellurium', 'tellurium_process.TelluriumProcess'),
]

CORE = ProcessTypes()

for process_name, process_path in PROCESSES_TO_REGISTER:
    module_name, class_name = process_path.rsplit('.', 1)
    try:
        import_statement = f'biosimulator_processes.processes.{module_name}'

        module = __import__(
             import_statement, fromlist=[class_name])

        # module = importlib.import_module(import_statement)

        # Get the class from the module
        bigraph_class = getattr(module, class_name)

        # Register the process
        CORE.process_registry.register(process_name, bigraph_class)
        print(f"{class_name} registered successfully.")
    except ImportError as e:
        print(f"{class_name} not available. Error: {e}")

