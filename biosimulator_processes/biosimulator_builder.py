from typing import *
from biosimulator_processes.builder import Builder
from biosimulator_processes import CORE


class BiosimulatorBuilder(Builder):
    def __init__(self, schema: Dict = None, tree: Dict = None, filepath: str = None):
        super().__init__(schema=schema, tree=tree, file_path=filepath, core=CORE)

