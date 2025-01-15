# -- step and process implementation references for registration --
from bsp.data_model.base import Implementation


# TODO: add the rest of the implementations here

COBRA_PROCESSES = [
    Implementation(
        address='cobra-process',
        location='processes.cobra_process.CobraProcess',
        dependencies=["cobra", "imageio"]
    ),
    Implementation(
        address='sed-cobra-process',
        location='processes.cobra_process.SedCobraProcess',
        dependencies=["cobra", "imageio"]
    ),
    Implementation(
        address='dynamic-fba',
        location='processes.cobra_process.DynamicFBA',
        dependencies=["cobra", "imageio"]

    )
]

COPASI_PROCESSES = [
    Implementation(
        address='copasi-process',
        location='processes.copasi_process.CopasiProcess',
        dependencies=["copasi-basico"]
    ),
    Implementation(
        address='sed-copasi-process',
        location='processes.copasi_process.SedCopasiProcess',
        dependencies=["copasi-basico"]
    )
]

SMOLDYN_PROCESSES = [
    Implementation(
        address='smoldyn-process',
        location='processes.smoldyn_process.SmoldynProcess',
        dependencies=["smoldyn"]
    ),
    Implementation(
        address='smoldyn-process',
        location='processes.smoldyn_process.SmoldynProcess',
        dependencies=["smoldyn"]
    )
]


TELLURIUM_PROCESSES = [
    Implementation(
        address='tellurium-process',
        location='processes.tellurium_process.TelluriumProcess',
        dependencies=["tellurium"]
    )
]

PROCESS_IMPLEMENTATIONS = COBRA_PROCESSES + COPASI_PROCESSES + SMOLDYN_PROCESSES + TELLURIUM_PROCESSES


STEP_IMPLEMENTATIONS = [
    Implementation(
        address='mongo-emitter',
        location='steps.main_steps.MongoDatabaseEmitter',
        dependencies=["pymongo"]
    )
    # ('output-generator', 'steps.main_steps.OutputGenerator'),
    # ('time-course-output-generator', 'steps.main_steps.TimeCourseOutputGenerator'),
    # ('smoldyn_step', 'steps.main_steps.SmoldynStep', ['smoldyn']),
    # ('simularium_smoldyn_step', 'steps.main_steps.SimulariumSmoldynStep', ['smoldyn', 'simulariumio']),
]

INITIAL_MODULES = PROCESS_IMPLEMENTATIONS + STEP_IMPLEMENTATIONS
