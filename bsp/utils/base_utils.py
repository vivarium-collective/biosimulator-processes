import traceback
import subprocess
import sys
import importlib
from dataclasses import dataclass
from pprint import pformat
from types import ModuleType
from typing import Optional


def handle_exception(error_key: str | Exception = "bio-compose-error") -> str:
    tb_str = traceback.format_exc()
    if isinstance(error_key, Exception):
        error_key = str(error_key)
    error_message = pformat(f"{error_key}:\n{tb_str}")
    return error_message


def handle_sbml_exception() -> str:
    return handle_exception("time-course-simulation-error")


@dataclass
class SimulatorImport:
    simulator_id: str
    module: Optional[ModuleType] = None


def dynamic_simulator_import(module_name: str) -> SimulatorImport:
    """
    Import a single simulator module at the highest level. For use in async dynamic env creation.

    :param module_name: (`str`) The name of the module to import.
    :return: (`SimulatorImport`) The imported simulator.
    """
    module = None
    try:
        module = __import__(module_name)
    except ImportError as e:
        print(e)

    return SimulatorImport(simulator_id=module_name, module=module)


def dynamic_simulator_install(simulators: list[str], verbose: bool = True):
    """
    Dynamically installs required simulator libraries.

    :param simulators: (`list[str]`) list of simulator libraries to install
    :param verbose: (`bool`) whether to print progress confirmations
    """
    for sim in simulators:
        try:
            # Check if the simulator is already installed
            importlib.import_module(sim)
            print(f"{sim} is already installed.") if verbose else None
        except ImportError:
            # Install using pip in the current environment
            print(f"Installing {sim}...") if verbose else None
            subprocess.check_call([sys.executable, "-m", "pip", "install", sim])
            print(f"{sim} installed successfully.") if verbose else None


def new_document(name, address, _type, config, inputs, outputs, add_emitter=True):
    doc = {
        name: {
            "address": f"local:{address}",
            "_type": _type,
            "config": config,
            "inputs": inputs,
            "outputs": outputs,
        }
    }

    if add_emitter:
        doc["emitter"] = {
            "address": f"local:ram-emitter",
            "_type": "step",
            "inputs": inputs
        }

    return doc
