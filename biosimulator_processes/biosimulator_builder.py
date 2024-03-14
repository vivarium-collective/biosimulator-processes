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
    def generate_input_kwargs(cls, **config_params) -> Dict[str, Any]:
        """Generate kwargs to be used as dynamic input for process configuration.

            Args:
                **config_params:`kwargs`: values that would be otherwise defined by the user
                    in the prompter input prompt can instead be defined as kwargs in this
                    method. PLEASE NOTE: each kwarg value
                    passed here should be a dictionary specifying the process name (according
                    to the registry ie: `'CopasiProcess'`), and the process config kwarg.

                    For example:

                        prompter.add_single_process(
                            CopasiProcess={
                                'model': {
                                    'model_source': {
                                        'value': 'BIOMD0000000391'}

            Returns:
                Dict[str, Any]: configuration kwargs for process construction.
        """
        input_kwargs = {**config_params}
        process_kwargs = input('Please enter the process configuration keyword arguments: ')
        process_args = process_kwargs.split(',')
        for arg in process_args:
            key, value = arg.split('=')
            try:
                # safely evaluate the value to its actual data type
                input_kwargs[key.strip()] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                input_kwargs[key] = value
        print(f'Input kwargs generated: {input_kwargs}')
        return input_kwargs

    def add_single_process(self, **config_params) -> None:
        """Add a single process to the bigraph via the builder. Config params
            can be passed in place of Prompter input prompts.

            Args:
                  **config_params:`kwargs`: to bypass this class' input prompts for kwarg-style
                    process configuration declaration, pass the kwarg you want and press
                    enter when prompted for the same kwarg. PLEASE NOTE: each kwarg value
                    passed here should be a dictionary specifying the process name (according
                    to the registry ie: `'CopasiProcess'`), and the process config kwarg.

                    For example:

                        prompter.add_single_process(
                            CopasiProcess={
                                'model': {
                                    'model_source': 'BIOMD0000000391'}

        """
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
        return

    def add_processes(self, num: int, **config_params) -> None:
        """Get prompted for adding `num` processes to the bigraph and visualize the composite.

            Args:
                num:`int`: number of processes to add.
                **config_params:`kwargs`: configuration params used in place of object
                    prompting. See `self.add_single_process()`. PLEASE NOTE:
                    There should be an extra layer of nesting as compared to the
                    single process add to specify on which n of `num` to add the
                    config params. For example:

                    prompter.add_single_process(
                            CopasiProcess={
                                1: {
                                    'model': {
                                        'model_source': 'BIOMD0000000391'}


            # TODO: Allow for kwargs to be passed in place of input vals for process configs
        """
        print('Run request initiated...')
        print(f'{num} processes will be added to the bi-graph.')

        if self.connect_all:
            print('All processes will be connected as well.')
        else:
            # TODO: implement this through kwargs
            print('Using edge configuration spec...')

        for n in range(num):
            single_config_params = {}
            for process_key, value in config_params:
                if num in value.keys():
                    single_config_params.update(**value[num])
                else:
                    single_config_params = {**config_params}
            self.add_single_process(**config_params)
        print('All processes added.')

        write_doc = self.yesno(input('Save composition to document? (y/n): '))
        if write_doc:
            doc = self.builder_instance.document()
            doc_fp = input('Please enter the save destination of this document: ')
            self.builder_instance.write(filename=doc_fp)
            print('Composition written to document!')

        # view composite
        print('This is the composite: ')
        return self.builder_instance.visualize()

    def generate_composite_run(self, duration: int = None, **params) -> None:
        """Generate and run a composite.

            Args:
                duration:`int`: the interval for which to run the composite.
        """
        if duration is None:
            duration = int(input('How long would you like to run this composite for?: '))

        print('Generating composite...')
        composite = self.builder_instance.generate()
        print('Composite generated!')
        print(f'Running generated composite for an interval of {duration}')
        results = composite.run(duration)  # TODO: add handle force complete
        print('Composite successfully run. Request complete. Done.')
        return results

    def start(self, num: int = None, **config_params):
        """Entrypoint to get prompted for input data with which to build the bigraph, then visualize
            and run the composite. All positional args and kwargs will be re-queried in the
            prompt if set to `None`. TODO: What other steps could possibly occur here? What about before?

            Args:
                num:`int`: number of processes to add. Defaults to `None`.
                **config_params:`kwargs`: see add_processes.
        """
        if num is None:
            num = int(input('How many processes would you like to add to the bigraph?'))
        return self.add_processes(num, **config_params)

    def run(self, num: int = None, duration: int = None, **params) -> None:
        """Entrypoint to get prompted for input data with which to build the bigraph, then visualize
            and run the composite. All positional args and kwargs will be requeried in the
            prompt if set to `None`. TODO: What other steps could possibly occur here? What about before?

            Args:
                num:`int`: number of processes to add. Defaults to `None`.
                duration:`int`: interval to run process composite for. Defaults to `None`.
                **params:`kwargs`: Custom params. TODO: implement these.
        """
        return self.generate_composite_run()

    @classmethod
    def yesno(cls, user_input: str) -> Union[bool, None]:
        return True if 'y' in user_input.lower() \
                else False if 'n' in user_input.lower() \
                else None



