from math import pi

import numpy as np
import rustworkx as rx
import networkx as nx
from qiskit_nature.second_q.hamiltonians.lattices import (
    BoundaryCondition,
    HyperCubicLattice,
    Lattice,
    LatticeDrawStyle,
    LineLattice,
    SquareLattice,
    TriangularLattice,
)
from qiskit_nature.second_q.hamiltonians import FermiHubbardModel
from qiskit_nature.second_q.problems import LatticeModelProblem
from qiskit_algorithms import NumPyMinimumEigensolver
from qiskit_nature.second_q.algorithms import GroundStateEigensolver
from qiskit_nature.second_q.mappers import JordanWignerMapper
from process_bigraph import Composite, Process
# TODO: import more qiskit nature for sbml processes here
from biosimulator_processes import CORE


class QiskitProcess(Process):
    config_schema = {
        'num_qbits': 'int',
        'duration': 'int'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

    def initial_state(self):
        return {}

    def inputs(self):
        return {}

    def outputs(self):
        return {}

    def update(self, state, interval):
        return {}


class QAOAProcess(QiskitProcess):
    config_schema = {
        'bigraph_instance': 'tree[any]'}

    def __init__(self, config=None, core=CORE):
        # TODO: Finish this based on https://qiskit-community.github.io/qiskit-algorithms/tutorials/05_qaoa.html
        super().__init__(config, core)
        self.num_nodes = len(list(self.config['bigraph_instance'].keys()))

        # TODO: Enable dynamic setting of these weights with np.stack
        weights = []
        for i, n in enumerate(list(range(self.num_nodes))):
            adj = [0.0, 1.0, 1.0, 0.0]  # TODO: Finish this
            weights.append(adj)

        self.w = np.stack(weights)
        w = np.array([
            [0.0, 1.0, 1.0, 0.0],
            [1.0, 0.0, 1.0, 1.0],
            [1.0, 1.0, 0.0, 1.0],
            [0.0, 1.0, 1.0, 0.0]])

        self.G = nx.from_numpy_array(w)
        print('Drawing graph: ')
        self._draw_graph()

    def _draw_graph(self):
        layout = nx.random_layout(self.G, seed=10)
        colors = ["r", "g", "b", "y"]
        nx.draw(self.G, layout, node_color=colors)
        labels = nx.get_edge_attributes(self.G, "weight")
        return nx.draw_networkx_edge_labels(self.G, pos=layout, edge_labels=labels)


class QuantumAutoencoderProcess(QiskitProcess):
    config_schema = {
        'num_qbits': 'int',
        'duration': 'int',
        'global_random_seed': {
            '_default': 42,
            '_type': 'string'
        }}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        """
            TODO: See https://qiskit-community.github.io/qiskit-machine-learning/tutorials/12_quantum_autoencoder.html
        """


class LatticeGroundStateSolverProcess(QiskitProcess):
    config_schema = {
        'num_nodes': 'int',
        'interaction_parameters': {
            '_type': 'tree[float]',
            '_default': {'t': -1.0, 'u': 5.0}},
        'onsite_potential': {  # <--alias for v
            '_default': 0.0,
            '_type': 'float'}}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

        num_nodes = self.config['num_nodes']
        boundary_condition = BoundaryCondition.OPEN
        line_lattice = LineLattice(num_nodes=num_nodes, boundary_condition=boundary_condition)
        interaction_parameters = self.config['interaction_parameters']
        t = interaction_parameters['t']
        u = interaction_parameters['u']
        v = self.config['onsite_potential']
        lattice = line_lattice.uniform_parameters(uniform_interaction=t, uniform_onsite_potential=v)
        fhm = FermiHubbardModel(lattice=lattice, onsite_interaction=u)
        self.lmp = LatticeModelProblem(fhm)

    def initial_state(self):
        return {}

    def inputs(self):
        """TODO: Take in instances of bigraphs and convert and then fit them into the Fermi Hubbard Model."""
        return {}

    def outputs(self):
        return {'ground_state': 'float'}

    def update(self, state, interval):
        numpy_solver = NumPyMinimumEigensolver()
        qubit_mapper = JordanWignerMapper()
        calc = GroundStateEigensolver(qubit_mapper, numpy_solver)
        res = calc.solve(self.lmp)
        print(res)
        # TODO: somehow be able to create a new instance from this ground state.
        return {'ground_state': res}
