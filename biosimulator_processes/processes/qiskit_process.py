from process_bigraph import Composite, Process
# TODO: import qiskit nature for sbml processes here
from biosimulator_processes import CORE


class QiskitProcess(Process):
    config_schema = {
        'num_qbits': 'int',
        'duration': 'int`'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
