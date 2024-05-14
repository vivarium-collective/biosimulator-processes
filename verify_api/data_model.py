from typing import *
from biosimulator_processes.data_model import BaseModel


class ProcessRegistrationData(BaseModel):
    reg_id: str


class AvailableProcesses(BaseModel):
    process_names: List[str]


class ODEComparison(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    timestamp: str
    outputs: List
