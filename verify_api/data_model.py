from typing import *
from biosimulator_processes.data_model import BaseModel


class ProcessRegistrationData(BaseModel):
    reg_id: str


class AvailableProcesses(BaseModel):
    process_names: List[str]


class ProcessAttributes(BaseModel):
    name: str
    initial_state: Dict
    input_schema: Dict
    output_schema: Dict


class ODEComparison(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    timestamp: str
    outputs: List


class UploadFileResponse(BaseModel):
    message: str
    file_location: str


class ODEComparisonMatrix(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    data: Dict
