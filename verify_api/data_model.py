from typing import *
from biosimulator_processes.data_model import BaseModel


class ODEComparison(BaseModel):
    duration: int
    num_steps: int
    biomodel_id: str
    timestamp: str
    outputs: List[Dict]