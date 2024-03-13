from builder import ProcessTypes
import importlib


# Define a list of processes to attempt to import and register
PROCESSES_TO_REGISTER = [
    ('cobra', 'cobra_process.CobraProcess'),
    ('copasi', 'copasi_process.CopasiProcess'),
    ('smoldyn', 'smoldyn_process.SmoldynProcess'),
    ('tellurium', 'tellurium_process.TelluriumProcess'),
    ('parameter_scan', 'parameter_scan.DeterministicTimeCourseParameterScan')
]

CORE = ProcessTypes()

for process_name, process_path in PROCESSES_TO_REGISTER:
    module_name, class_name = process_path.rsplit('.', 1)
    try:
        if 'parameter_scan' in process_name:
            import_statement = f'biosimulator_processes.steps.{module_name}'
        else:
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


"""
 Builder(dataclasses) <- Implementation(dict) <- ProcessBigraph(dict) <- BigraphSchema(dict) 
"""
