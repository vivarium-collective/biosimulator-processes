import importlib
from typing import *

from bsp.data_model import schemas
from bsp.registration import Registrar
from bsp.implementations import INITIAL_MODULES


VERBOSE_REGISTRATION = True
ATTEMPT_INSTALL = False


# project-scoped process/implementation registrar
app_registrar = Registrar()


#  register types:
for schema_name in schemas.__all__:
    schema = getattr(schemas, schema_name)
    app_registrar.register_type(schema_name, schema)


# register implementations of steps and processes:
app_registrar.register_initial_modules(
    items_to_register=INITIAL_MODULES,
    verbose=VERBOSE_REGISTRATION,
    attempt_install=ATTEMPT_INSTALL
)









