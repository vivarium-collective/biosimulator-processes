"""Comparator Step:

    Here the entrypoint is the results of an emitter.
"""

from process_bigraph import Step, pp

from biosimulator_processes import CORE


class ODEComparatorStep(Step):
    config_schema = {}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

    def inputs(self):
        return {'data': 'string'}

    def outputs(self):
        return {'comparison': 'string'}

    def update(self, state):
        return {'comparison': state['data']}