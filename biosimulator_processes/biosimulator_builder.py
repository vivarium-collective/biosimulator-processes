from typing import *
from builder import Builder
from biosimulator_processes import CORE


class BiosimulatorBuilder(Builder):
    def __init__(self, schema: Dict, tree: Dict, filepath: str):
        super().__init__(schema=schema, tree=tree, file_path=filepath, core=CORE)

