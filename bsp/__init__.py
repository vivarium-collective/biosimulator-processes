from bsp.schemas import config, types
from bsp.registration import Registrar
from bsp.implementations import INITIAL_MODULES


VERBOSE_REGISTRATION = False
ATTEMPT_INSTALL = False


# project-scoped process/implementation registrar
app_registrar = Registrar()


#  register types:
app_registrar.register_initial_types(
    config=config,
    types=types,
    verbose=VERBOSE_REGISTRATION
)


# register implementations of steps and processes:
app_registrar.register_initial_modules(
    items_to_register=INITIAL_MODULES,
    verbose=VERBOSE_REGISTRATION,
    attempt_install=ATTEMPT_INSTALL
)









