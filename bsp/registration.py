import dataclasses
import os
from typing import *

from process_bigraph import ProcessTypes

from bsp.utils.base_utils import dynamic_simulator_install
from bsp.data_model.base import Implementation, Type


@dataclasses.dataclass
class ImplementationRegistry:
    id: str
    implementation: ProcessTypes
    primary: bool


class SimulatorDependency(str):
    pass


class Registrar(object):
    registries: List[ImplementationRegistry]
    core: ProcessTypes
    registered_addresses: List[str]
    implementation_dependencies: Dict[str, List[SimulatorDependency]]

    def __init__(self, core: ProcessTypes = None):
        self.core = core or ProcessTypes()
        self.registries = []

        default_reg = ImplementationRegistry(
            id="default",
            implementation=ProcessTypes(),
            primary=True
        )
        self.add_registry(default_reg)
        self.set_primary(default_reg.id)
        self.core.type_registry = self.core.types()
        self.initial_registration_complete = False
        self.implementation_dependencies = {}

    @property
    def registered_addresses(self) -> List[str]:
        return list(self.core.process_registry.registry.keys())

    def add_registry(self, registry: ImplementationRegistry):
        if registry.primary:
            for registry in self.registries:
                if registry.primary is not None:
                    registry.primary = False

            self.core = registry.implementation

        self.registries.append(registry)

    def set_primary(self, registry_id: str):
        for registry in self.registries:
            # take away existing primary
            if registry.primary:
                registry.primary = False

            # set ref as primary
            if registry.id == registry_id:
                registry.primary = True
                self.core = registry.implementation

    def register_type(self, type_id: str, type_schema: Dict):
        self.core.register_types({type_id: type_schema})

    def register_process(self, address: str, implementation: object, verbose=False) -> None:
        type_registry = self.core
        type_registry.process_registry.register(address, implementation)
        if verbose:
            print(f"Successfully registered {implementation} to address: {address}")

    def register_module(self, implementation: Implementation, verbose=False, attempt_install=False) -> None:
        library, module_name, class_name = implementation.location.rsplit('.', 3)
        try:
            # library = 'steps' if 'process' not in path else 'processes'
            import_statement = f'bsp.{library}.{module_name}'
            module = __import__(
                 import_statement, fromlist=[class_name])
            bigraph_class = getattr(module, class_name)
            self.core.process_registry.register(implementation.address, bigraph_class)
        except Exception as e:
            if verbose:
                print(f"Cannot register {class_name}. Error:\n**\n{e}\n**")
            if attempt_install:
                dynamic_simulator_install(simulators=[library])

    def register_initial_modules(
            self,
            items_to_register: List[Implementation],
            package: str = "bsp",
            verbose=False,
            attempt_install=False
    ) -> None:
        if not self.initial_registration_complete:
            for implementation in items_to_register:
                self.register_module(implementation=implementation, verbose=verbose, attempt_install=attempt_install)
                process_deps = [SimulatorDependency(dep) for dep in implementation.dependencies]
                self.implementation_dependencies[implementation.address] = process_deps
            self.initial_registration_complete = True
