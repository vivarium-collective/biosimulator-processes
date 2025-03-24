from dataclasses import dataclass, asdict
from typing import Any, Optional

from backend.runner.data_model.base import Base 


@dataclass
class SimulationRequest(Base):
    """
    Data structure representing the client request recieved by the python runner translated from the SimulationRequest gRPC message struct
    """
    job_id: str
    timestamp: str
    duration: int
    document: dict[str, Any]
    status: str = "PENDING:SUBMITTED"

    @property
    def serialized(self):
        return asdict(self)