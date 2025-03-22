from dataclasses import dataclass, field, asdict 
from typing import Any, Optional 

from backend.runner.data_model.base import Base


@dataclass
class BaseSimulationResponse(Base):
    job_id: str
    status: str
    timestamp: str 


@dataclass 
class IntervalResponse(BaseSimulationResponse):
    """
    :param job_id: (`str`)
    :param status: (`str`)
    :param timestamp: (`str`)
    :param interval_id: (`str`)
    :param results: (`dict[str, Any]`)
    """
    results: dict[str, Any]
    interval_id: int
    

