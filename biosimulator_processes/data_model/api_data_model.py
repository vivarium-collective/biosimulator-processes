"""TODO: Migrate compare data model and others here"""


from dataclasses import dataclass
from typing import *

from biosimulator_processes.data_model import _BaseClass
from biosimulator_processes.api.run import plot_ode_output_data


# TODO: use this in server
@dataclass
class ODESimulationOutput(_BaseClass):
    t: List[float]
    floating_species: Dict[str, List[float]]

    def __init__(self, data: Dict):
        self.data = data
        self.t = data['time']
        self.floating_species = {
            name: output
            for name, output in data['floating_species'].items()}

    def plot(self, sample_size: None):
        return plot_ode_output_data(self.data, sample_size=sample_size)
