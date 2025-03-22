from dataclasses import dataclass, asdict 


@dataclass 
class Base:
    @property
    def serialized(self):
        return asdict(self)
    