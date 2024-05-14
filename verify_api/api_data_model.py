from typing import *

from biosimulator_processes.data_model import BaseModel
from biosimulator_processes.data_model.compare_data_model import ODEComparisonResult


class ProcessRegistrationData(BaseModel):
    reg_id: str


class AvailableProcesses(BaseModel):
    process_names: List[str]


class ODEProcessIntervalResult(BaseModel):
    interval_id: float
    copasi_floating_species_concentrations: Dict[str, float]
    tellurium_floating_species_concentrations: Dict[str, float]
    amici_floating_species_concentrations: Dict[str, float]
    time: float


class ODEComparison(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    timestamp: str
    outputs: Optional[List[ODEProcessIntervalResult]]
