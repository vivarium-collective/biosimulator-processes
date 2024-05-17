"""Data Model Root for Biosimulator Processes

author: Alex Patrie < alexanderpatrie@gmail.com >
license: Apache 2.0
created: 03/2024
"""


from dataclasses import dataclass, asdict, field

import numpy as np
from pydantic import BaseModel, ConfigDict


@dataclass
class _BaseClass:
    def to_dict(self):
        return asdict(self)


class _BaseModel(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)


class DescriptiveArray(np.ndarray):
    """Array with metadata."""

    def __new__(cls, array, dtype=None, order=None, description: str = None, metadata: dict = None, **kwargs):
        obj = np.asarray(array, dtype=dtype, order=order).view(cls)
        metadata = metadata or kwargs
        metadata['description'] = description
        obj.metadata = metadata
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.metadata = getattr(obj, 'metadata', None)
