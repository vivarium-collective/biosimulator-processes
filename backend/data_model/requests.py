from dataclasses import dataclass, asdict 


@dataclass
class SimulationRequest:
    job_id: str
    last_updated: str
    duration: int
    spec: dict
    status: str

    @property
    def serialized(self):
        return asdict(self)