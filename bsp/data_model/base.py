"""
Base data model relating to utils, files, protocols, etc.
"""


from dataclasses import dataclass, asdict, Field
from typing import List

from pydantic import ConfigDict, BaseModel as _BaseModel


class BaseModel(_BaseModel):
    """Base Pydantic Model with custom app configuration"""
    model_config = ConfigDict(arbitrary_types_allowed=True)


@dataclass
class BaseClass:
    """Base Python Dataclass multipurpose class with custom app configuration."""
    def to_dict(self):
        return asdict(self)


@dataclass
class FilePath(BaseClass):
    name: str
    path: str


# --- INSTALLATION
@dataclass
class DependencyFile(BaseClass):
    name: str
    hash: str


@dataclass
class InstallationDependency(BaseClass):
    name: str
    version: str
    markers: str = Field(default='')  # ie: "markers": "platform_system == \"Windows\""
    # files: List[DependencyFile] = Field(default=[])


@dataclass
class Simulator(BaseClass):
    name: str  # name installed by pip
    version: str
    deps: List[InstallationDependency]

