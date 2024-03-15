from typing import *
import ast
import requests
from pydantic import BaseModel
from graphviz import Digraph
from process_bigraph import Composite
from builder import Builder
from biosimulator_processes import CORE
from biosimulator_processes.data_model import _BaseClass


class BiosimulatorBuilder(Builder):
    _is_initialized = False

    def __init__(self, schema: Dict = None, tree: Dict = None, filepath: str = None):
        if not self._is_initialized:
            super().__init__(schema=schema, tree=tree, file_path=filepath, core=CORE)


class BuildPrompter:
    """Front-End user interaction controller for high-level BioBuilder API."""
    builder_instance: Union[Builder, BiosimulatorBuilder] = None
    connect_all: bool = True

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
                                    'model_source': 'BIOMD0000000391'}

            Returns:
                Dict[str, Any]: configuration kwargs for process construction.
        """
        input_kwargs = {**config_params}
        process_kwargs = input('No config kwargs have yet been generated. Please enter the process configuration keyword arguments. Press enter to skip: ')
        if process_kwargs:
            process_args = process_kwargs.split(",")
            for i, arg in enumerate(process_args):
                arg = arg.strip()
                key, value = arg.split('=')
                try:
                    # safely evaluate the value to its actual data type
                    input_kwargs[key.strip()] = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    input_kwargs[key] = value
        print(f'Input kwargs generated: {input_kwargs}')
        return input_kwargs

    def add_single_process(self,
                           builder: Union[Builder, BiosimulatorBuilder] = None,
                           process_type: str = None,
                           config: _BaseClass = None,
                           builder_node_name: str = None) -> None:
        """Get prompted through the steps of adding a single process to the bigraph via the builder."""
        if self.builder_instance is None:
            self.builder_instance = builder or BiosimulatorBuilder()

        if not process_type:
            process_type = input(
                f'Please enter one of the following process types that you wish to add:\n{self.builder_instance.list_processes()}\n:')

        if not builder_node_name:
            builder_node_name = input('Please enter the name that you wish to assign to this process: ')

        # generate input data from user prompt results and add processes to the bigraph  through pydantic model
        DynamicProcessConfig = self.builder_instance.get_pydantic_model(process_type)

        input_kwargs = self.generate_input_kwargs() if config is None else config.to_dict()
        dynamic_config = DynamicProcessConfig(**input_kwargs)
        self.builder_instance.add_process(
            process_id=builder_node_name,
            name=process_type,
            config=dynamic_config)  # {**input_kwargs})

        print(f'{builder_node_name} process successfully added to the bi-graph!')

        if self.connect_all:
            self.builder_instance.connect_all()
            print(f'All nodes including the most recently added {builder_node_name} processes connected!')

        print(f'Done adding single {builder_node_name} ({process_type}) to the bigraph.')
        return

    def add_processes(self,
                      num: int,
                      builder: Union[Builder, BiosimulatorBuilder] = None,
                      config: _BaseClass = None,
                      write_doc: bool = False) -> None:
        """Get prompted for adding `num` processes to the bigraph and visualize the composite.

            Args:
                num:`int`: number of processes to add.
                builder:`Builder`: instance with which we add processes to bigraph
                config: used if not wanting to use input prompts. For now, this applies the same
                    config to each `num` of processes added. TODO: Expand this.
                write_doc: whether to write the doc. You will be re-prompted if False.

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
            self.add_single_process(builder=builder, config=config)
        print('All processes added.')

        if not write_doc:
            write_doc = self.yesno(input('Save composition to document? (y/n): '))
        if write_doc:
            doc = self.builder_instance.document()
            doc_fp = input('Please enter the save destination of this document: ')
            self.builder_instance.write(filename=doc_fp)
            print('Composition written to document!')

        # view composite
        print('This is the composite: ')
        return self.visualize_bigraph()

    def generate_engine(self, builder: Builder = None) -> Composite:
        builder = builder or self.builder_instance
        return builder.generate()

    def generate_composite_run(self, duration: int = None, **run_params) -> None:
        """Generate and run a composite.

            Args:
                duration:`int`: the interval for which to run the composite.
        """
        if duration is None:
            duration = int(input('How long would you like to run this composite for?: '))

        print('Generating composite...')

        engine = self.generate_engine()
        print('Composite generated!')

        print(f'Running generated composite for an interval of {duration}')

        results = engine.run(duration)  # TODO: add handle force complete
        print('Composite successfully run. Request complete. Done.')
        return results

    def start(self, num: int = None):
        """Entrypoint to get prompted for input data with which to build the bigraph, then visualize
            and run the composite. All positional args and kwargs will be re-queried in the
            prompt if set to `None`. TODO: What other steps could possibly occur here? What about before?

            Args:
                num:`int`: number of processes to add. Defaults to `None`.
        """
        if num is None:
            num = int(input('How many processes would you like to add to the bigraph?'))
        return self.add_processes(num)

    def run(self, duration: int = None, **run_params) -> None:
        """Entrypoint to get prompted for input data with which to build the bigraph, then visualize
            and run the composite. All positional args and kwargs will be re-queried in the
            prompt if set to `None`. TODO: What other steps could possibly occur here? What about before?

            Args:
                duration:`int`: interval to run process composite for. Defaults to `None`.
                **run_params:`kwargs`: Custom params. TODO: implement these.
        """
        return self.generate_composite_run(duration=duration, **run_params)

    def execute(self, num: int = None, duration: int = None, **run_params) -> None:
        """For use as the highest level function called by the BioBuilder REST API."""
        self.start(num)
        return self.run(duration, **run_params)

    def write_bigraph(self, fp: str, output_dir='out'):
        """Use the builder instance attribute to write out the bigraph document to a fp."""
        return self.builder_instance.write(filename=fp, outdir=output_dir)

    def wipe_builder(self):
        self.builder_instance = None
        print(f'Builder flushed! This is verified because builder is: {self.builder_instance}')

    def flush(self, out_dir='out', fp: str = None, write: bool = True) -> None:
        """Optionally write the bigraph to document and wipe the current builder_instance instance.

            Args:
                out_dir:`str`: destination to which we save the document.
                fp:`str`: path by which to save if write is true. Defaults to None.
                write:`bool`: whether to write out the document before wiping. Defaults to `True`.
        """
        from datetime import datetime
        if write:
            if fp is None:
                fp = f"BUILD_FLUSH_{str(datetime.now()).replace(' ', '__').replace(':', '_')}"
            self.write_bigraph(fp, out_dir)
        return self.wipe_builder()

    def visualize_bigraph(self):
        return self.builder_instance.visualize()

    @classmethod
    def yesno(cls, user_input: str) -> Union[bool, None]:
        return True if 'y' in user_input.lower() \
                else False if 'n' in user_input.lower() \
                else None



