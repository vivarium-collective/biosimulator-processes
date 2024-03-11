import os
import json
import pprint
import warnings
from biosimulator_processes.bigraph_schema.registry import get_path, set_path, deep_merge
from biosimulator_processes.bigraph_schema import Edge
from biosimulator_processes.bigraph_schema.protocols import local_lookup_module
from biosimulator_processes.process_bigraph import Process, Step, Composite, ProcessTypes
from biosimulator_processes.bigraph_viz.diagram import plot_bigraph
from pydantic import create_model, BaseModel


pretty = pprint.PrettyPrinter(indent=2)


def pf(x):
    return pretty.pformat(x)


def node_from_tree(
        builder,
        schema,
        tree,
        path=()
):
    # TODO -- this might need to use core.fold()
    node = BuilderNode(builder, path)
    if isinstance(tree, dict):
        for key, subtree in tree.items():
            next_path = path + (key,)
            node.branches[key] = node_from_tree(
                builder=builder,
                schema=schema.get(key, schema) if schema else {},
                tree=subtree,
                path=next_path)

    return node


class BuilderNode:

    def __init__(self, builder, path):
        self.builder = builder
        self.path = path
        self.branches = {}

    def __repr__(self):
        tree = self.value()
        return f"BuilderNode({pf(tree)})"

    def __getitem__(self, keys):
        # Convert single key to tuple
        keys = (keys,) if isinstance(keys, (str, int)) else keys
        head = keys[0]
        if head not in self.branches:
            self.branches[head] = BuilderNode(
                builder=self.builder,
                path=self.path + (head,))

        tail = keys[1:]
        if len(tail) > 0:
            return self.branches[head].__getitem__(tail)
        else:
            return self.branches[head]

    def __setitem__(self, keys, value):
        # Convert single key to tuple
        keys = (keys,) if isinstance(keys, (str, int)) else keys
        head = keys[0]
        tail = keys[1:]
        path_here = self.path + (head,)

        if head not in self.branches:
            self.branches[head] = BuilderNode(
                builder=self.builder,
                path=path_here)

        if len(tail) > 0:
            self.branches[head].__setitem__(tail, value)
        elif isinstance(value, dict):
            if '_type' in value:
                set_path(
                    tree=self.builder.schema,
                    path=path_here,
                    value=value['_type'])

            if '_value' in value:
                set_path(
                    tree=self.builder.tree,
                    path=path_here,
                    value=value['_value'])

                self.branches[head] = BuilderNode(
                    builder=self.builder,
                    path=path_here)

            else:
                self.branches[head] = node_from_tree(
                    builder=self.builder,
                    schema=self.schema(),
                    tree=value,
                    path=path_here)
        else:
            # set the value
            set_path(tree=self.builder.tree, path=path_here, value=value)

    def update(self, state):
        self.builder.tree = deep_merge(self.builder.tree, state)
        self.builder.complete()

    def value(self):
        return get_path(self.builder.tree, self.path)

    def schema(self):
        return get_path(self.builder.schema, self.path)

    def top(self):
        return self.builder.node

    def add_process(
            self,
            name,
            config=None,
            inputs=None,
            outputs=None,
            **kwargs
    ):
        """ Add a process to the tree """
        # TODO -- assert this process is in the process_registry
        assert name, 'add_process requires a name as input'
        process_class = self.builder.core.process_registry.access(name)

        # Check if config is a Pydantic model and convert to dict if so
        if isinstance(config, BaseModel):
            config = config.model_dump()
        else:
            config = config or {}
        config.update(kwargs)

        # what edge type is this? process or step
        edge_type = 'process'
        if issubclass(process_class, Step):
            edge_type = 'step'

        # make the process spec
        state = {
            '_type': edge_type,
            'address': f'local:{name}',  # TODO -- only support local right now?
            'config': config,
            'inputs': {} if inputs is None else inputs,
            'outputs': {} if outputs is None else outputs,
        }

        set_path(tree=self.builder.tree, path=self.path, value=state)
        self.builder.complete()

    def connect(self, port=None, target=None):
        value = self.value()
        schema = self.schema()
        assert self.builder.core.check('edge', value), "connect only works on edges"

        if port in schema['_inputs']:
            value['inputs'][port] = target
        if port in schema['_outputs']:
            value['outputs'][port] = target

    def connect_all(self, append_to_store_name='_store'):
        # Check if the current node is an edge and perform connections if it is
        value = self.value()
        if self.builder.core.check('edge', value):
            schema = self.schema()
            for port in schema.get('_inputs', {}).keys():
                if port not in value.get('inputs', {}):
                    value['inputs'][port] = [port + append_to_store_name]
            for port in schema.get('_outputs', {}).keys():
                if port not in value.get('outputs', {}):
                    value['outputs'][port] = [port + append_to_store_name]
            # Optionally, update the current node value here if necessary

        # Recursively apply connect_all to all child nodes
        for child in self.branches.values():
            child.connect_all(append_to_store_name=append_to_store_name)

    def interface(self, print_ports=False):
        value = self.value()
        schema = self.schema()
        if not self.builder.core.check('edge', value):
            warnings.warn(f"Expected '_type' to be in {EDGE_KEYS}, found '{tree_type}' instead.")
        elif self.builder.core.check('edge', value):
            process_ports = {}
            process_ports['_inputs'] = schema.get('_inputs', {})
            process_ports['_outputs'] = schema.get('_outputs', {})
            if not print_ports:
                return process_ports
            else:
                print(pf(process_ports))

    def emit(self, key=None, port=None):
        if key is None:
            key =  port
        value = self.value()
        schema = self.schema()
        if self.builder.core.check('edge', value):
            inputs = value.get('inputs', {})
            outputs = value.get('outputs', {})
            inputs_schema = schema.get('_inputs', {})
            outputs_schema = schema.get('_outputs', {})

            if not port:
                # connect to all ports
                for prt, val in inputs_schema.items():
                    self.builder.node['emitter', 'config', 'emit', prt] = val
                for prt, val in outputs_schema.items():
                    self.builder.node['emitter', 'config', 'emit', prt] = val
            elif port in inputs_schema:
                # update the emitter config
                self.builder.node['emitter', 'config', 'emit'].value().update({key: inputs_schema[port]})
                self.builder.node['emitter', 'inputs', key] = list(self.path[:-1]) + list(inputs[port])
                self.builder.node['emitter'].schema()['_inputs'].update({key: inputs_schema[port]})

            elif port in outputs_schema:
                self.builder.node['emitter', 'config', 'emit'].update({key: outputs_schema[port]})
                self.builder.node['emitter', 'inputs', key] = list(self.path[:-1]) + list(outputs[port])
                self.builder.node['emitter'].schema()['_inputs'].update({key: outputs_schema[port]})

            else:
                raise Exception(f"can not connect port {port}. available ports for this edge include {inputs_schema.keys()} {outputs_schema.keys()}")
        else:
            # emit the path
            self.builder.node['emitter', 'config', 'emit', key] = schema
            self.builder.node['emitter', 'inputs', key] = self.path


class Builder:

    def __init__(
            self,
            schema=None,
            tree=None,
            core=None,
            emitter='ram-emitter',
            file_path=None,
    ):
        schema = schema or {}
        tree = tree or {}

        if file_path:
            with open(file_path, 'r') as file:
                graph_data = json.load(file)
                tree = deep_merge(tree, graph_data)

        self.core = core or ProcessTypes()
        self.schema, self.tree = self.core.complete(schema, tree)
        self.node = node_from_tree(self, self.schema, self.tree)
        self.add_emitter(emitter=emitter)


    def __repr__(self):
        return f"Builder({pf(self.tree)})"

    def __getitem__(self, keys):
        return self.node[keys]

    def __setitem__(self, keys, value):
        self.node.__setitem__(keys, value)
        self.complete()


    def get_pydantic_model(self, process_name):
        """
        Fetches the Pydantic model for the given process name from the process_registry.

        Args:
            process_name (str): The name of the process whose Pydantic model is requested.

        Returns:
            Pydantic model class for the requested process configuration schema.
        """
        if hasattr(self.core.process_registry, 'get_pydantic_model'):
            return self.core.process_registry.get_pydantic_model(process_name)
        else:
            raise NotImplementedError("Process registry does not support Pydantic model retrieval.")


    def add_emitter(self, emitter='ram-emitter'):
        """
        key is the node id for the emitter, at the top level
        name is the emitter type
        """
        # hardcode that emitter is called "emitter"
        self.node['emitter'].add_process(
            name=emitter,
            config={'emit': {}},
            inputs={},
        )

    def update(self, state):
        self.node.update(state)

    def list_types(self):
        return self.core.type_registry.list()

    def list_processes(self):
        return self.core.process_registry.list()

    def complete(self):
        self.schema, self.tree = self.core.complete(self.schema, self.tree)

    def connect_all(self, append_to_store_name='_store'):
        self.node.connect_all(append_to_store_name=append_to_store_name)

    def visualize(self, filename=None, out_dir=None, **kwargs):
        return plot_bigraph(
            state=self.tree,
            schema=self.schema,
            core=self.core,
            out_dir=out_dir,
            filename=filename,
            **kwargs)

    def generate(self):
        composite = Composite({
            'state': self.tree,
            'composition': self.schema},
            core=self.core)
        self.tree = composite.state
        self.schema =composite.composition
        return composite

    def document(self):
        return self.core.serialize(
            self.schema,
            self.tree)

    def write(self, filename, outdir='out'):
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        filepath = f"{outdir}/{filename}.json"
        document = self.document()

        # Writing the dictionary to a JSON file
        with open(filepath, 'w') as json_file:
            json.dump(document, json_file, indent=4)

        print(f"File '{filename}' successfully written in '{outdir}' directory.")

    def register_type(self, key, schema):
        self.core.type_registry.register(key, schema)

    def register_process(self, process_name, address=None):
        """
        Register processes into the local core type system
        """
        assert isinstance(process_name, str), f'Process name must be a string: {process_name}'

        if address is None:  # use as a decorator
            def decorator(cls):
                if not issubclass(cls, Edge):
                    raise TypeError(f"The class {cls.__name__} must be a subclass of Edge")
                self.core.process_registry.register(process_name, cls)
                return cls
            return decorator

        else:
            # Check if address is a string
            # TODO -- we want to also support remote processes with non local protocol
            if isinstance(address, str):
                process_class = local_lookup_module(address)
                self.core.process_registry.register(process_name, process_class)

            # Check if address is a class object
            elif issubclass(address, Edge):
                self.core.process_registry.register(process_name, address)
            else:
                raise TypeError(f"Unsupported address type for {process_name}: {type(address)}. Registration failed.")



def test_builder():
    from biosimulator_processes.process_bigraph.experiments.minimal_gillespie import GillespieEvent, EXPORT  # , GillespieInterval

    core = ProcessTypes()
    core.import_types(EXPORT)  # TODO -- make this better

    initial_tree = {
        'DNA_store': {
            '_type': 'map[float]',
            'A gene': 2.0,
            'B gene': 1.0},
        'mRNA_store': {
            '_type': 'map[float]',
            'A mRNA': 0.0,
            'B mRNA': 0.0},
    }

    builder = Builder(core=core, tree=initial_tree)

    # test set/get
    builder['DNA_store', 'C gene'] = 3.0
    assert builder['DNA_store', 'C gene'].value() == 3.0

    builder['down', 'here'] = {
        '_value': 10,
        '_type': 'integer'}

    x = builder['down', 'here']
    assert x.value() == 10

    # add processes
    print(f"available processes: {builder.list_processes()}")

    ## register processes by name: what processes do we want and where do they come from
    builder.register_process(
        'GillespieEvent', GillespieEvent)
    builder.register_process(
        'GillespieInterval',
        address='process_bigraph.experiments.minimal_gillespie.GillespieInterval',
    )

    ## add processes
    builder['event_process'].add_process(
        name='GillespieEvent',
        kdeg=1.0,  # kwargs fill parameters in the config
    )
    builder['interval_process'].add_process(
        name='GillespieInterval',
        # inputs={'port_id': ['store']}  # we should be able to set the wires directly like this
    )

    ## print the ports
    print(f"EVENT PROCESS PORTS: {pf(builder['event_process'].interface())}")
    print(f"INTERVAL PROCESS PORTS: {pf(builder['interval_process'].interface())}")

    # make bigraph-viz diagram before connect
    builder.visualize(filename='builder_test1',
                      show_values=True,
                      show_types=True)

    # connect processes
    # builder['event_process'].connect(port='DNA', target=['DNA_store'])
    # builder['event_process'].connect(port='mRNA', target=['mRNA_store'])
    # builder['interval_process'].connect(port='DNA', target=['DNA_store'])
    # builder['interval_process'].connect(port='mRNA', target=['mRNA_store'])
    builder['interval_process'].connect(port='interval', target=['event_process', 'interval'])  # TODO -- viz  needs to show interval in process
    builder['interval_process'].connect_all(append_to_store_name='_store')
    builder['event_process'].connect_all(append_to_store_name='_store')
    # builder.connect_all(append_to_store_name='_store')

    # make bigraph-viz diagram after connect
    builder.visualize(filename='builder_test2',
                      show_values=True,
                      show_types=True)

    # we can turn on the emits through a port
    # builder.add_emitter()
    builder['interval_process'].emit(port='DNA')
    builder['interval_process'].emit(port='mRNA')



    # update state
    update_state = {
        'DNA_store': {
            'A gene': 3.0,
            # 'B gene': 1.0
        },
    }
    builder.update(update_state)

    # make bigraph-viz diagram after updated state
    builder.visualize(filename='builder_test3',
                      show_values=True,
                      show_types=True)

    # make composite, simulate
    composite = builder.generate()
    composite.run(10)

    results = composite.gather_results()

    print(f"RESULTS: {results}")

    # save document
    builder.write(filename='builder_test_doc')

    # load builder from document
    builder2 = Builder(core=core, file_path='out/builder_test_doc.json')
    builder2.visualize(filename='builder_test4',
                      show_values=True,
                      show_types=True)


def test_pydantic():
    from biosimulator_processes.process_bigraph.experiments.minimal_gillespie import GillespieEvent, GillespieInterval, EXPORT  #

    core = ProcessTypes()
    core.import_types(EXPORT)  # TODO -- make this better

    # make the builder
    builder = Builder(core=core)

    ## register processes by name: what processes do we want and where do they come from
    builder.register_process(
        'GillespieEvent', GillespieEvent)
    builder.register_process(
        'GillespieInterval', GillespieEvent)

    # get a pydantic model
    model = builder.get_pydantic_model('GillespieEvent')
    config = model(kdeg=1.0)
    builder['event_process'].add_process(name='GillespieEvent', config=config)


def test_data_model(builder, process_name: str, process_class: object, **kwargs):
    builder.register_process(
        process_name, process_class)

    # get a pydantic model
    model = builder.get_pydantic_model(process_name)
    config = model(**kwargs)
    builder['event_process'].add_process(name=process_name, config=config)
    return builder


if __name__ == '__main__':
    # test_builder()
    test_pydantic()
