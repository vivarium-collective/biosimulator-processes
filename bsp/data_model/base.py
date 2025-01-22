"""
Base data model relating to utils, files, protocols, etc.
"""


from dataclasses import dataclass, asdict, Field, field
from types import FunctionType
from typing import List, Dict, Union

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
    markers: str  # ie: "markers": "platform_system == \"Windows\""
    # files: List[DependencyFile] = Field(default=[])


@dataclass
class Simulator(BaseClass):
    name: str  # name installed by pip
    version: str
    deps: List[InstallationDependency]


@dataclass
class Implementation(BaseClass):
    address: str
    location: str
    dependencies: List[str]


@dataclass
class Type(BaseClass):
    address: str
    schema: Dict[str, Union[str, FunctionType]]

