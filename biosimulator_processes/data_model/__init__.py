"""Data Model Root for Biosimulator Processes

author: Alex Patrie < alexanderpatrie@gmail.com >
license: Apache 2.0
created: 03/2024
"""


from dataclasses import dataclass, asdict, field
from pydantic import BaseModel, ConfigDict


@dataclass
class _BaseClass:
    def to_dict(self):
        return asdict(self)


class _BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
