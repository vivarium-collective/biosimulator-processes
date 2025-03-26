from dataclasses import dataclass, field, asdict 
from typing import Any, Optional 

from backend.runner.data_model.base import Base, BaseModel


class ResponseModel(BaseModel):
    """
    :param job_id: (`str`)
    :param status: (`str`)
    :param timestamp: (`str`)
    :param interval_id: (`str`)
    :param results: (`dict[str, Any]`)
    """
    job_id: str
    status: str
    timestamp: str 
    results: Any
    interval_id: int
    status: str

  
@dataclass
class BaseSimulationResponse(Base):
    job_id: str
    status: str
    timestamp: str 


@dataclass 
class IntervalResponse(Base):
    """
    :param job_id: (`str`)
    :param status: (`str`)
    :param timestamp: (`str`)
    :param interval_id: (`str`)
    :param results: (`dict[str, Any]`)
    """
    job_id: str
    status: str
    timestamp: str 
    results: Any
    interval_id: int
    status: str
    

