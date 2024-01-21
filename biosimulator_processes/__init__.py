from process_bigraph import process_registry

# Attempt to import and register CobraProcess
try:
    from biosimulator_processes.cobra_process import CobraProcess
    process_registry.register('cobra', CobraProcess)
except ImportError:
    print("CobraProcess not available.")

# Attempt to import and register CopasiProcess
try:
    from biosimulator_processes.copasi_process import CopasiProcess
    process_registry.register('copasi', CopasiProcess)
except ImportError:
    print("CopasiProcess not available.")

# Attempt to import and register SmoldynProcess
try:
    from biosimulator_processes.smoldyn_process import SmoldynProcess
    process_registry.register('smoldyn', SmoldynProcess)
except ImportError:
    print("SmoldynProcess not available.")

# Attempt to import and register TelluriumProcess
try:
    from biosimulator_processes.tellurium_process import TelluriumProcess
    process_registry.register('tellurium', TelluriumProcess)
except ImportError:
    print("TelluriumProcess not available.")