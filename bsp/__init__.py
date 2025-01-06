import importlib
from typing import *

from bsp.data_model.schemas import SEDModelType, TimeCourseConfigType
from bsp.registration import Registrar


# -- step and process implementation references for registration --

STEP_IMPLEMENTATIONS = [
    # ('output-generator', 'steps.main_steps.OutputGenerator'),
    # ('time-course-output-generator', 'steps.main_steps.TimeCourseOutputGenerator'),
    # ('smoldyn_step', 'steps.main_steps.SmoldynStep', ['smoldyn']),
    # ('simularium_smoldyn_step', 'steps.main_steps.SimulariumSmoldynStep', ['smoldyn', 'simulariumio']),
    ('mongo-emitter', 'steps.main_steps.MongoDatabaseEmitter', ["pymongo"]),
]

PROCESS_IMPLEMENTATIONS = [
    # ('cobra-process', 'processes.cobra_process.CobraProcess'),
    # ('copasi-process', 'processes.copasi_process.CopasiProcess'),
    # ('tellurium-process', 'processes.tellurium_process.TelluriumProcess'),
    # ('utc-amici', 'processes.amici_process.UtcAmici'),
    # ('utc-copasi', 'processes.copasi_process.UtcCopasi'),
    # ('utc-tellurium', 'processes.tellurium_process.UtcTellurium'),
    ('ode', 'bundles.dfba.ODECopasi', ["copasi-basico"]),
    ('fba', 'bundles.dfba.FBA', ["cobra", "imageio"])
]

VERBOSE_REGISTRATION = False
ATTEMPT_INSTALL = False


# process/implementation registrar
app_registrar = Registrar()

# register types
app_registrar.register_type("sed_model", SEDModelType().to_dict())
app_registrar.register_type("utc_config", TimeCourseConfigType().to_dict())

# attempt to add smoldyn implementations
try:
    import smoldyn
    # PROCESS_IMPLEMENTATIONS.append(('smoldyn-process', 'smoldyn_process.SmoldynProcess'))
    # PROCESS_IMPLEMENTATIONS.append(('smoldyn-io-process', 'smoldyn_process.SmoldynIOProcess'))
except:
    if VERBOSE_REGISTRATION:
        print('Smoldyn is not properly installed in this environment and thus its process implementation cannot be registered. Please consult smoldyn documentation.')

# register implementations of steps and processes
items_to_register = STEP_IMPLEMENTATIONS + PROCESS_IMPLEMENTATIONS

app_registrar.register_initial_modules(
    items_to_register=items_to_register,
    verbose=VERBOSE_REGISTRATION,
    attempt_install=ATTEMPT_INSTALL
)









