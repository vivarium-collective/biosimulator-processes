from typing import List, Dict, Tuple, Any
from pydantic import BaseModel as _Base, ConfigDict


class BaseModel(_Base):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class SimulatorComparisonResult(BaseModel):
    simulators: List[str]
    value: Dict[Tuple[str], Dict[str, Any]]


class IntervalResult(BaseModel):
    global_time_stamp: float
    results: Dict[str, Any]


class SimulatorResult(BaseModel):
    process_id: str
    simulator: str
    result: List[IntervalResult]


class ComparisonResults(BaseModel):
    duration: int
    num_steps: int
    values: List[SimulatorResult]


class ProcessAttributes(BaseModel):
    name: str
    initial_state: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


class CompositeRunError(BaseModel):
    exception: Exception
