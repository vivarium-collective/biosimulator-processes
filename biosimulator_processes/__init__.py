import importlib

from builder import ProcessTypes
from bigraph_schema import TypeSystem
from process_bigraph import Composite


# Define a list of processes to attempt to import and register
PROCESSES_TO_REGISTER = [
    ('cobra', 'cobra_process.CobraProcess'),
    ('copasi', 'copasi_process.CopasiProcess'),
    ('smoldyn', 'smoldyn_process.SmoldynProcess'),
    ('tellurium', 'tellurium_process.TelluriumProcess'),
]

# core process registry implementation (unique to this package)
CORE = ProcessTypes()

# register processes to CORE
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


# core type system implementation (unique to this package)
TYPE_SYSTEM = TypeSystem()
TYPE_SYSTEM.type_registry.register('composition', {'_default': Composite})  # is this valid?
