import importlib
from typing import *

from process_bigraph import ProcessTypes

from bsp.data_model.sed import MODEL_TYPE, UTC_CONFIG_TYPE
from bsp.registry import Registrar





try:
    import smoldyn
    PROCESS_IMPLEMENTATIONS.append(('smoldyn-process', 'smoldyn_process.SmoldynProcess'))
    PROCESS_IMPLEMENTATIONS.append(('smoldyn-io-process', 'smoldyn_process.SmoldynIOProcess'))
except:
    print('Smoldyn is not properly installed in this environment and thus its process implementation cannot be registered. Please consult smoldyn documentation.')


# process/implementation registrar
registrar = Registrar()

# register types
registrar.register_type("sed_model", MODEL_TYPE)
registrar.register_type("utc_config", UTC_CONFIG_TYPE)

# register implementations of steps and processes
registrar.register_initial_modules(
    items_to_register=STEP_IMPLEMENTATIONS + PROCESS_IMPLEMENTATIONS
)




