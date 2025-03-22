from dataclasses import dataclass, asdict
from typing import Any, Optional

from backend.runner.data_model.base import Base 


@dataclass
class SimulationRequest(Base):
    """
    Data structure representing the full request made by the Client through (for example), React
    """
    job_id: str
    timestamp: str
    duration: int
    document: dict[str, Any]
    status: str = "PENDING"

    @property
    def serialized(self):
        return asdict(self)