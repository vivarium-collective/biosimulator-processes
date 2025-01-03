import importlib
from typing import *

from bsp.data_model.sed import MODEL_TYPE, UTC_CONFIG_TYPE
from bsp.registration import Registrar


# -- step and process implementation references for registration --

STEP_IMPLEMENTATIONS = [
    ('output-generator', 'main.OutputGenerator'),
    ('time-course-output-generator', 'main.TimeCourseOutputGenerator'),
    ('smoldyn_step', 'main.SmoldynStep'),
    ('simularium_smoldyn_step', 'main.SimulariumSmoldynStep'),
    ('mongo-emitter', 'main.MongoDatabaseEmitter'),
    ('copasi-step', 'ode_simulation.CopasiStep'),
    ('tellurium-step', 'ode_simulation.TelluriumStep'),
    ('amici-step', 'ode_simulation.AmiciStep'),
    ('plotter', 'viz.CompositionPlotter'),
    ('plotter2d', 'viz.Plotter2d'),
    ('utc-comparator', 'comparator_step.UtcComparator'),
    ('smoldyn-step', 'bio_compose.SmoldynStep'),
    ('simularium-smoldyn-step', 'bio_compose.SimulariumSmoldynStep'),
    ('database-emitter', 'bio_compose.MongoDatabaseEmitter')
]

PROCESS_IMPLEMENTATIONS = [
    ('cobra-process', 'cobra_process.CobraProcess'),
    ('copasi-process', 'copasi_process.CopasiProcess'),
    ('tellurium-process', 'tellurium_process.TelluriumProcess'),
    ('utc-amici', 'amici_process.UtcAmici'),
    ('utc-copasi', 'copasi_process.UtcCopasi'),
    ('utc-tellurium', 'tellurium_process.UtcTellurium')
]

VERBOSE_REGISTRATION = False


# process/implementation registrar
app_registrar = Registrar()

# register types
app_registrar.register_type("sed_model", MODEL_TYPE)
app_registrar.register_type("utc_config", UTC_CONFIG_TYPE)

# attempt to add smoldyn implementations
try:
    import smoldyn
    PROCESS_IMPLEMENTATIONS.append(('smoldyn-process', 'smoldyn_process.SmoldynProcess'))
    PROCESS_IMPLEMENTATIONS.append(('smoldyn-io-process', 'smoldyn_process.SmoldynIOProcess'))
except:
    if VERBOSE_REGISTRATION:
        print('Smoldyn is not properly installed in this environment and thus its process implementation cannot be registered. Please consult smoldyn documentation.')

# register implementations of steps and processes
app_registrar.register_initial_modules(
    items_to_register=STEP_IMPLEMENTATIONS + PROCESS_IMPLEMENTATIONS,
    verbose=VERBOSE_REGISTRATION
)









