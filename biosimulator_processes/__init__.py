from builder import ProcessTypes


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
        # Dynamically import the module
        process_module = __import__(
            f'biosimulator_processes.processes.{module_name}', fromlist=[class_name])
        # Get the class from the module
        process_class = getattr(process_module, class_name)

        # Register the process
        CORE.process_registry.register(class_name, process_class)
        print(f"{class_name} registered successfully.")
    except ImportError as e:
        print(f"{class_name} not available. Error: {e}")
