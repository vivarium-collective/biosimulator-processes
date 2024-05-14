from typing import *
from biosimulator_processes.data_model import BaseModel


class ProcessRegistrationData(BaseModel):
    process_registration_id: str


class AvailableProcesses(BaseModel):
    names: List[ProcessRegistrationData]


class ODEComparison(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    timestamp: str
    outputs: List
