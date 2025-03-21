from dataclasses import dataclass, field, asdict 
from typing import Any 


@dataclass
class SimulationResponse:
    job_id: str
    last_updated: str
    status: str
    interval: float | int
    results: dict[str, Any] = field(default_factory={})

    @property
    def serialized(self):
        return asdict(self)
