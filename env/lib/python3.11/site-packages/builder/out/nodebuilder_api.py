"""
Bigraph Builder
================

API for building process bigraphs, integrating bigraph-schema, process-bigraph, and bigraph-viz under an intuitive
Python API.
"""

from process_bigraph import Process, Composite, process_registry, types
from bigraph_viz import plot_bigraph
import pprint

pretty = pprint.PrettyPrinter(indent=2)


def pf(x):
    return pretty.pformat(x)


class Node(dict):

    def __init__(self, id=None, value=None, type=None):
        super().__init__()

        # TODO -- should the type constrain the value? We should check the type
        # TODO -- can we do better than importing types from process_bigraph? local_types?
        type_schema = types.access(type)
        dict_value = {
                '_value': value,
                '_type': type,
            }

        if id:
            self[id] = dict_value
        else:
            pass

    def add_process(
            self,
            id,
            type='process',
            address=None,
            config=None,
            inputs=None,
            outputs=None,
    ):
        assert types.access(type), f'type "{type}" is not found in the types registry'

        # TODO -- assert that the process is in the process registry?

        address = address or f'local:{type}'
        self[id] = {
            '_type': type or 'process',
            'address': address,
            'config': config or {},
            'wires': {
                'inputs': inputs or {},
                'outputs': outputs or {},
            },
        }


class Builder(Node):

    def __init__(self, tree=None, nodes=None):
        super().__init__()
        self.tree = tree or {}
        if nodes:
            for node_id, spec in nodes.items():
                path = spec.get('path')
                value = spec.get('value')
                type = spec.get('type')

                # TODO -- check the type here? or in Node?
                self[path] = Node(
                    id=node_id,
                    value=value,
                    type=type
                )

        self.processes = {}  # TODO retrieve this from tree_dict?
        self.types = {}  # TODO -- schemas need to go in here.

    def __setitem__(self, keys, value):
        # Convert single key to tuple
        keys = (keys,) if isinstance(keys, str) else keys

        # Navigate through the keys, creating nested dictionaries as needed
        d = self.tree
        for key in keys[:-1]:  # iterate over keys to create the nested structure
            if key not in d:
                d[key] = Node()
            d = d[key]
        d[keys[-1]] = value  # set the value at the final level

    def __getitem__(self, keys):
        # Convert single key to tuple
        keys = (keys,) if isinstance(keys, str) else keys

        d = self.tree
        for key in keys:
            d = d[key]  # move deeper into the dictionary
        return d

    def __repr__(self):
        return f"{pf(self.tree)}"

    def make_composite(self):
        return Composite({'state': self.tree})

    def check(self):
        self.make_composite()  # this should check consistency

    def infer(self):
        composite = self.make_composite()  # Composite makes the inference upon init
        self.tree = composite.state
        return self.tree

    def plot_graph(self, **kwargs):
        return plot_bigraph(self.tree, **kwargs)


def test_builder():
    nodes = Node().add_process('a')

    nodes = {
        'a': {
            'value': 1.0,
            'type': 'conc',
            'path': ['path', 'to']
        }
    }

    a = Builder(
        nodes=nodes,
        tree={},
    )



    # Testing the Builder class
    b = Builder()
    b['path', 'to', 'node'] = 1.0
    print(b.tree)

    # Accessing the value
    value = b['path', 'to', 'node']
    print(value)

    b['path', 'b2', 'c'] = 12.0
    print(b)

    b.add_process(id='process1')
    b['path', 'to'].add_process(id='p1', type='example_type', address='')
    print(b['path'])


    # print(b.state)  # this should be the state hierarchy
    print(b.processes)  # This should be the process registry
    # print(b['path', 'b2', 'c'].type)  # access schema keys
    #
    # b['path', 'to', 'p1'].connect(port_id='', target=['path', '1'])  # connect port, with checking

    b.check()  # check if everything is connected
    b.infer()  # fill in missing content
    b.plot_graph()  # bigraph-viz

    b

def build_gillespie():

    gillespie = Builder()
    gillespie.add_process(type='event', protocol='local', rate_param=1.0, wires={})  # protocol local should be default. kwargs could fill the config
    gillespie.add_process(type='interval')

    print(gillespie['event'].interface())
    gillespie['event'].connect(port='DNA', target=['DNA_store'])
    gillespie['DNA_store'] = {'C': 2.0}  # this should check the type

    gillespie.compile()  # this fills and checks, this should also connect ports to stores with the same name, at the same level
    gillespie.plot()
    composite_data = gillespie.composite()  # get the document
    gillespie.write(filename='gillespie1')  # save the document

    gillespie.run()

    results = gillespie.get_results()







def test_builder_demo():

    sed_schema = {
        'models': {},
        'algorithms': {},
        'visualizations': {},
        'tasks': {},
    }
    a = Builder(tree=sed_schema)

    # or
    b = Builder()
    b['models'] = {}
    b['algorithms'] = {}
    b['visualizations'] = {}
    b['tasks'] = {}

    # b.add_process(id='p1', address=':', config={}, inputs={}, outputs={})





if __name__ == '__main__':
    test_builder()
    test_builder_demo()
