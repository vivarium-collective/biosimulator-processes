from typing import *
from dataclasses import dataclass

from biosimulator_processes.data_model import BaseModel
from biosimulator_processes.data_model.compare_data_model import ODEComparisonResult


class ProcessRegistrationData(BaseModel):
    reg_id: str


class AvailableProcesses(BaseModel):
    process_names: List[str]


@dataclass
class ODEComparison(BaseModel, ODEComparisonResult):
    def __init__(self, **kwargs):
        super(ODEComparison, self).__init__(**kwargs)