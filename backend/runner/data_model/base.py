from dataclasses import dataclass, asdict 

from pydantic import BaseModel as PydanticBase, ConfigDict


class BaseModel(PydanticBase):
    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True)

    
@dataclass 
class Base:
    @property
    def serialized(self):
        return asdict(self)
    