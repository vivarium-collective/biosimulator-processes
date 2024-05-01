from typing import List, Dict, Tuple, Any
from pydantic import BaseModel


class SimulatorComparisonResult(BaseModel):
    simulators: List[str]
    value: Dict[Tuple[str], Dict[Any]]


class CompositeRunError(BaseModel):
    exception: Exception
