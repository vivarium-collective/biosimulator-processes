from typing import List, Dict, Tuple, Any
from pydantic import BaseModel as _Base, ConfigDict


class BaseModel(_Base):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class SimulatorComparisonResult(BaseModel):
    simulators: List[str]
    value: Dict[Tuple[str], Dict[str, Any]]


class ProcessAttributes:
    name: str
    initial_state: Dict[str, Any]


class CompositeRunError(BaseModel):
    exception: Exception
