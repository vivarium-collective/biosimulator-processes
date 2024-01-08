from process_bigraph import process_registry
from biosimulator_processes.cobra_process import CobraProcess
from biosimulator_processes.copasi_process import CopasiProcess
from biosimulator_processes.tellurium_process import TelluriumProcess  # , TelluriumStep
from biosimulator_processes.smoldyn_process import SmoldynProcess


# register processes
process_registry.register('cobra', CobraProcess)
process_registry.register('copasi', CopasiProcess)
process_registry.register('smoldyn', SmoldynProcess)
process_registry.register('tellurium', TelluriumProcess)

# TODO: Eventually integrate this Step implementation
# process_registry.register('tellurium_step', TelluriumStep)

