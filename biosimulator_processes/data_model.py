from typing import Dict, List, Union, Tuple, Optional, Any
from types import NoneType
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pydantic import (
    BaseModel as _BaseModel,
    field_validator,
    field_serializer,
    Field,
    ConfigDict,
    create_model,
    ValidationError
)


__all__ = [
    'SpeciesChanges',
    'GlobalParameterChanges',
    'ReactionParameter',
    'ReactionChanges',
    'TimeCourseModelChanges',
    'ModelSource',
    'BiomodelId',
    'ModelFilepath',
    'TimeCourseModel',
    'ProcessConfigSchema',
    'PortSchema',
    'EmittedType',
    'EmitterConfig',
    'EmitterInstance',
    'TimeCourseProcessInstance',
    'FromDict',
    'BasicoModelChanges',
    'SedModel',
    'BaseModel',
    'ModelParameter',
    '__ProcessConfig',
    'Port',
    'State',
    'dynamic_process_config',
    'TimeCourseProcessConfig'
]


# TODO: Parse this into sep. library datamodels


@dataclass
class _BaseClass:
    def to_dict(self):
        return asdict(self)


@dataclass
class ModelParameter(_BaseClass):
    """
        Attributes:
            name:`str`
            feature:`str`
            value:`Union[float, int, str]`
            scope:`str`
    """
    name: str
    feature: str
    value: Union[float, int, str]
    scope: str


@dataclass
class SpeciesChanges(_BaseClass):  # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
    name: str
    unit: Union[str, NoneType, ModelParameter] = Field(default=None)
    initial_concentration: Optional[Union[float, ModelParameter]] = Field(default=None)
    initial_particle_number: Optional[Union[float, NoneType, ModelParameter]] = Field(default=None)
    initial_expression: Union[str, NoneType, ModelParameter] = Field(default=None)
    expression: Union[str, NoneType, ModelParameter] = Field(default=None)


@dataclass
class GlobalParameterChanges(_BaseClass):  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
    name: str
    initial_value: Union[float, NoneType] = Field(default=None)
    initial_expression: Union[str, NoneType] = Field(default=None)
    expression: Union[str, NoneType] = Field(default=None)
    status: Union[str, NoneType] = Field(default=None)
    param_type: Union[str, NoneType] = Field(default=None)  # ie: fixed, assignment, reactions, etc


@dataclass
class ReactionParameter(_BaseClass):
    parameter_name: str
    value: Union[float, int, str]


@dataclass
class ReactionModelParameter(ModelParameter):
    """
        Attributes:
            name:`str`
            feature:`str`
            value:`Union[float, int, str]`
            scope:`str` = 'reaction'
    """
    scope: str = 'reaction'


@dataclass
class ReactionChanges(_BaseClass):
    """
        Attributes:
            reaction_name:`str`: name of the reaction you wish to change.
            parameter_changes:`List[ReactionParameter]`: list of parameters you want to change from
                `reaction_name`. Defaults to `[]`, which denotes no parameter changes.

    """
    reaction_name: str
    parameter_changes: List[ReactionParameter] = None
    reaction_scheme: Union[NoneType, str] = None


@dataclass
class TimeCourseModelChanges(_BaseClass):
    species_changes: List[SpeciesChanges] = None
    global_parameter_changes: List[GlobalParameterChanges] = None
    reaction_changes: List[ReactionChanges] = None


@dataclass
class ModelSource(_BaseClass):
    value: str

    @abstractmethod
    def validate_source(self):
        pass


@dataclass
class BiomodelID(ModelSource):
    def __init__(self, value):
        super().__init__(value)
        self.validate_source()

    def validate_source(self):
        if 'BIO' not in self.value:
            raise AttributeError('You must pass a valid biomodel id.')


@dataclass
class ModelFilepath(ModelSource):
    def __init__(self):
        self.validate_source()

    def validate_source(self):
        if '/' not in self.value:
            raise AttributeError('You must pass a valid model path.')


@dataclass
class ModelChange(_BaseClass):
    name: str
    scope: str
    value: Dict


@dataclass
class ModelChanges(_BaseClass):
    species_changes: List[ModelChange]
    param_changes: List[ModelChange]
    reaction_changes: List[ModelChange]


class ModelUnit:
    def __init__(self, **unit_config):
        for k, v in unit_config:
            self.__setattr__(k, v)


@dataclass
class SedModel(_BaseClass):
    model_source: Union[BiomodelID, ModelFilepath, str]

    def set_id(self, model_id):
        if model_id is None:
            if isinstance(self.model_source, str):
                modId = self.model_source
            else:
                modId = self.model_source.value
            return f'{modId}_Model'

    def to_dict(self):
        return asdict(self)


class TimeCourseModel(SedModel):
    """The data model declaration for process configuration schemas that support SED.

        Attributes:
            model_id: `str`
            model_source: `Union[biosimulator_processes.data_model.ModelFilepath, biosimulator_processes.data_model.BiomodelId]`
            model_language: `str`
            model_name: `str`
            model_changes: `biosimulator_processes.data_model.TimeCourseModelChanges`
    """
    model_language: str = 'sbml'
    model_name: str = 'Unnamed TimeCourse Model'
    model_changes: ModelChanges = None
    model_units: List[ModelUnit] = None

    def __init__(self,
                 model_source,
                 model_id=None,
                 model_language=model_language,
                 model_changes=model_changes,
                 model_units=model_units):
        """
            Parameters:
                model_source:`Union[str, ModelFilepath, BiomodelID`
                model_id:`str`
        """
        super().__init__(model_source)
        self.model_id = self.set_id(model_id)
        self.model_language = model_language
        self.model_changes = model_changes
        self.model_units = model_units


def dynamic_process_config(name: str = None, config: Dict = None, **kwargs):
    config = config or {}
    config.update(kwargs)
    dynamic_config_types = {}
    for param_name, param_val in config.items():
        dynamic_config_types[param_name] = (type(param_val), ...)

    model_name = 'ProcessConfig'
    if name is not None:
        proc_name = name.replace(name[0], name[0].upper())
        dynamic_name = proc_name + model_name
    else:
        dynamic_name = model_name

    DynamicProcessConfig = create_model(__model_name=dynamic_name, **dynamic_config_types)

    return DynamicProcessConfig(**config)


class Port(_BaseClass):
    value: Dict


# --- INSTALLATION
@dataclass
class DependencyFile(_BaseClass):
    name: str
    hash: str


@dataclass
class InstallationDependency(_BaseClass):
    name: str
    version: str
    markers: str = Field(default='')  # ie: "markers": "platform_system == \"Windows\""
    files: List[DependencyFile] = Field(default=[])


@dataclass
class Simulator(_BaseClass):
    name: str  # name installed by pip
    version: str
    deps: List[InstallationDependency]


# --- Non-Pydantic FromDict classes
class FromDict(dict):
    def __init__(self, value: Dict):
        super().__init__(value)


class BasicoModelChanges(FromDict):
    BASICO_MODEL_CHANGES_TYPE = {
        'species_changes': {
            'species_name': {
                'unit': 'maybe[string]',
                'initial_concentration': 'maybe[float]',
                'initial_particle_number': 'maybe[float]',
                'initial_expression': 'maybe[string]',
                'expression': 'maybe[string]'
            }
        },
        'global_parameter_changes': {
            'global_parameter_name': {
                'initial_value': 'maybe[float]',
                'initial_expression': 'maybe[string]',
                'expression': 'maybe[string]',
                'status': 'maybe[string]',
                'type': 'maybe[string]'  # (ie: fixed, assignment, reactions)
            }
        },
        'reaction_changes': {
            'reaction_name': {
                'parameters': {
                    'reaction_parameter_name': 'maybe[int]'  # (new reaction_parameter_name value)  <-- this is done with set_reaction_parameters(name="(REACTION_NAME).REACTION_NAME_PARAM", value=VALUE)
                },
                'reaction_scheme': 'maybe[string]'   # <-- this is done like set_reaction(name = 'R1', scheme = 'S + E + F = ES')
            }
        }
    }

    def __init__(self, _type: Dict = BASICO_MODEL_CHANGES_TYPE):
        super().__init__(_type)


class SedModel(FromDict):
    """
        # examples
            # changes = {
            #     'species_changes': {
            #         'A': {
            #             'initial_concent': 24.2,
            #             'b': 'sbml'
            #         }
            #     }
            # }
            #
            # r = {
            #     'reaction_name': {
            #         'parameters': {
            #             'reaction_parameter_name': 23.2
            #         },
            #         'reaction_scheme': 'maybe[string]'
            #     }
            # }
    """
    # The first 3 params are NOT optional below for a TimeCourseModel in SEDML. model_source has been adapted to mean point of residence
    MODEL_TYPE = {
        'model_id': 'string',
        'model_source': 'dict[string]',  # 'string',    # could be used as the "model_file" or "biomodel_id" below (SEDML l1V4 uses URIs); what if it was 'model_source': 'sbml:model_filepath'  ?
        'model_language': {    # could be used to load a different model language supported by COPASI/basico
            '_type': 'string',
            '_default': 'sbml'    # perhaps concatenate this with 'model_source'.value? I.E: 'model_source': 'MODEL_LANGUAGE:MODEL_FILEPATH' <-- this would facilitate verifying correct model fp types.
        },
        'model_name': {
            '_type': 'string',
            '_default': 'composite_process_model'
        },
        'model_changes': {
            'species_changes': 'maybe[tree[string]]',   # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
            'global_parameter_changes': 'maybe[tree[string]]',  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
            'reaction_changes': 'maybe[tree[string]]'
        },
        'model_units': 'maybe[tree[string]]'
    }

    def __init__(self, _type: Dict = MODEL_TYPE):
        super().__init__(_type)


MODEL_TYPE = {
        'model_id': 'string',
        'model_source': 'string',  # 'tree[string]',
        'model_language': {
            '_type': 'string',
            '_default': 'sbml'
        },
        'model_name': {
            '_type': 'string',
            '_default': 'composite_process_model'
        },
        'model_changes': {
            'species_changes': 'maybe[tree[string]]',
            'global_parameter_changes': 'maybe[tree[string]]',
            'reaction_changes': 'maybe[tree[string]]'
        },
        'model_units': 'maybe[tree[string]]'
    }
