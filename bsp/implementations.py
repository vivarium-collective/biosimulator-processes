# -- step and process implementation references for registration --

PROCESS_IMPLEMENTATIONS = [
    ('cobra-process', 'processes.cobra_process.CobraProcess', ["cobra", "imageio"]),
    ('copasi-process', 'processes.copasi_process.CopasiProcess', ["copasi-basico"]),
    ('smoldyn-process', 'processes.smoldyn_process.SmoldynProcess', ["smoldyn"]),
    # ('tellurium-process', 'processes.tellurium_process.TelluriumProcess'),
    # ('utc-amici', 'processes.amici_process.UtcAmici'),
    # ('utc-copasi', 'processes.copasi_process.UtcCopasi'),
    # ('utc-tellurium', 'processes.tellurium_process.UtcTellurium'),
]

STEP_IMPLEMENTATIONS = [
    ('mongo-emitter', 'steps.main_steps.MongoDatabaseEmitter', ["pymongo"]),
    # ('output-generator', 'steps.main_steps.OutputGenerator'),
    # ('time-course-output-generator', 'steps.main_steps.TimeCourseOutputGenerator'),
    # ('smoldyn_step', 'steps.main_steps.SmoldynStep', ['smoldyn']),
    # ('simularium_smoldyn_step', 'steps.main_steps.SimulariumSmoldynStep', ['smoldyn', 'simulariumio']),
]

INITIAL_MODULES = PROCESS_IMPLEMENTATIONS + STEP_IMPLEMENTATIONS
