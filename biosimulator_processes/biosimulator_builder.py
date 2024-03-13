from typing import *
import ast
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


class BuildPrompter:
    def __init__(self, builder_instance: Union[Builder, BiosimulatorBuilder]):
        self.builder_instance = builder_instance

    @classmethod
    def generate_input_kwargs(cls) -> Dict[str, Any]:
        """Generate kwargs to be used as dynamic input for process configuration.

            Args:
                None.
            Returns:
                Dict[str, Any]: configuration kwargs for process construction.
        """
        process_kwargs = input('Please enter the process configuration keyword arguments: ')
        process_args = process_kwargs.split(',')
        input_kwargs = {}
        for arg in process_args:
            key, value = arg.split('=')
            try:
                # safely evaluate the value to its actual data type
                input_kwargs[key.strip()] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                input_kwargs[key] = value
        print(input_kwargs)
        return input_kwargs

    def add_single_process(self):
        process_type = input(
            f'Please enter one of the following process types that you wish to add:\n{self.builder_instance.list_processes()}\n:')
        builder_node_name = input('Please enter the name that you wish to assign to this process: ')
        input_kwargs = self.generate_input_kwargs()
        visualize = input('Do you wish to visualize this addition after (y/N): ')
        self.builder_instance.add_process(process_id=builder_node_name, name=process_type, config={**input_kwargs})
        self.builder_instance.connect_all()
        if 'N' in visualize:
            self.builder_instance.visualize()
