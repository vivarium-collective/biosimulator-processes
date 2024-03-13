from typing import *
from builder import Builder
from biosimulator_processes import CORE


class BiosimulatorBuilder(Builder):
    _instance = None
    _is_initialized = False

    def __init__(self, schema: Dict = None, tree: Dict = None, filepath: str = None):
        if not self._is_initialized:
            super().__init__(schema=schema, tree=tree, file_path=filepath, core=CORE)
            # Perform your initialization here
            self._is_initialized = True

    def __new__(cls, *args, **kwargs):
        if not cls._is_initialized:
            if not cls._instance:
                cls._instance = super(BiosimulatorBuilder, cls).__new__(cls, *args, **kwargs)
            return cls._instance
        else:
            raise RuntimeError('Only one instance of this class can be created at a time.')


# class BiosimulatorBuilder(Builder):
#     def __init__(self, schema: Dict = None, tree: Dict = None, filepath: str = None):
#         super().__init__(schema=schema, tree=tree, file_path=filepath, core=CORE)
