from typing import *
import ast
from graphviz import Digraph
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
    def __init__(self,
                 builder_instance: Union[Builder, BiosimulatorBuilder],
                 num_additions: int,
                 connect_all: bool = True,
                 edge_config: Dict[str, str] = None,
                 auto_run: bool = False,
                 **additional_params):
        """
            Parameters:
                builder_instance:`Union[builder.Builder, BiosimulatorBuilder]`: builder object
                    instance on which to base the bigraph on.
                num_additions:`int`: number of processes to add and subsequently connect to the
                    bigraph composition.
                connect_all:`bool`: whether to use Builder.connect_all after adding processes. Defaults
                    to `True`.
                edge_config:`Dict[str, str]`: configuration details for edge/vertex connection if
                    `connect_all` is set to `False`. Defaults to `None`.
                auto_run:`bool`: Whether to automatically begin the prompting and running
                    of the build. If set to `True`, BuildPrompter.run() is called last during
                    object construction. Defaults to `False`.
                **additional_params:`kwargs`: addition/custom parameter specifications.
                    Options include: duration (how long to run the composite for)
                    TODO: make more use cases for this.
        """
        self.builder_instance = builder_instance
        self.connect_all = connect_all
        print('New prompter instance created!')
        if auto_run:
            print('Autorun is turned on. Now starting...')
            self.run(num=num_additions, duration=additional_params.get('duration'))

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
        print(f'Input kwargs generated: {input_kwargs}')
        return input_kwargs

    def add_single_process(self) -> None:
        process_type = input(
            f'Please enter one of the following process types that you wish to add:\n{self.builder_instance.list_processes()}\n:')
        builder_node_name = input('Please enter the name that you wish to assign to this process: ')

        input_kwargs = self.generate_input_kwargs()
        self.builder_instance.add_process(
            process_id=builder_node_name,
            name=process_type,
            config={**input_kwargs})
        print(f'{builder_node_name} process successfully added to the bi-graph!')

        if self.connect_all:
            self.builder_instance.connect_all()
            print(f'All nodes including the most recently added {builder_node_name} processes connected!')

        print(f'Done adding single {builder_node_name} ({process_type}) to the bigraph.')
        # while True:
        #     visualize = input('Do you wish to visualize this addition after (y/n): ')
        #     if 'y' in visualize.lower():
        #         print('Visualizing bigraph...')
        #         self.builder_instance.visualize()
        #         break
        #     elif 'n' or 'y' not in visualize.lower():
        #         print('Please enter a valid choice: (y/n)')
        #         continue
        #     else:
        #         print(f'Done adding single {builder_node_name} ({process_type}) to the bigraph.')
        #         break
        return

    def add_processes(self, num: int) -> Digraph:
        """Get prompted for adding `num` processes to the bigraph and visualize the composite.

            Args:
                num:`int`: number of processes to add.

            Returns:
                graphviz.Digraph visualization
        """
        # add processes
        print('Run request initiated...')
        if num is None:
            num = input('How many processes would you like to add to the bigraph?')
        print(f'{num} processes will be added to the bi-graph.')

        # handle connections
        if self.connect_all:
            print('All processes will be connected as well.')
        else:
            # TODO: implement this
            print('Using edge configuration spec...')

        for n in range(num):
            self.add_single_process()
        print('All processes added.')

        # view composite
        print('This is the composite that will be run: ')
        return self.builder_instance.visualize()

    def run(self, num: int = None, duration: int = None, **params) -> None:
        """Get prompted for input data with which to build the bigraph, then visualize
            and run the composite. All positional args and kwargs will be requeried in the
            prompt if set to `None`.

            Args:
                num:`int`: number of processes to add. Defaults to `None`.
                duration:`int`: interval to run process composite for. Defaults to `None`.
                **params:`kwargs`: Custom params. TODO: implement these.
        """

        # TODO: What other steps could possibly occur here? What about before?

        # run composite
        if duration is None:
            duration = int(input('How long would you like to run this composite for?: '))

        print('Generating composite...')
        composite = self.builder_instance.generate()
        print('Composite generated!')
        print(f'Running generated composite for an interval of {duration}')
        results = composite.run(duration)  # TODO: add handle force complete
        print('Composite successfully run. Request complete. Done.')


