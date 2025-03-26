import json 
from functools import partial

from vivarium.vivarium import Vivarium

from bsp import app_registrar

core = app_registrar.core

def from_doc(doc):
    return Vivarium(
        processes=core.process_registry.registry ,
        types=core.types(),
        core=core,
        document=doc
    )


# v = Vivarium(
#     processes=core.process_registry.registry ,
#     types=core.types(),
#     core=core
# )
# 
# v.add_process(
#     name='Tx',
#     process_id='tx',
#     config={
#         'ktsc': 22.2,
#         'kdeg': -0.11,
#         'k': 0.001
#     },
#     inputs={
#         'DNA': ['DNA'],
#         'mRNA': ['mRNA']
#     },
#     outputs={
#         'DNA': ['DNA'],
#         'mRNA': ['mRNA'],
#         'dC': ['dC']
#     }
# )

# doc1 = v.make_document()
# v2 = from_doc(doc=doc1)
# v2.add_emitter()

import os

def example():
    fixturepath = '/Users/alexanderpatrie/Desktop/repos/biosimulator-processes/tests/requests/membrane_composite.json'
    with open(fixturepath, 'r') as f:
        return json.load(f)

EXAMPLE = example()

# def write_example():
#     with open('./example.json', 'w') as f:
#         json.dump(v2.make_document(), f, indent=4)