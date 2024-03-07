from typing import Dict, List, Union, Tuple, Optional
from types import NoneType
from abc import ABC, abstractmethod
from pydantic import BaseModel as _BaseModel, field_validator, field_serializer, Field, ConfigDict


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
    'CopasiProcessConfig',
    'PortSchema',
    'EmittedType',
    'EmitterConfig',
    'EmitterInstance',
    'ProcessInstance',
    'FromDict',
    'BasicoModelChanges',
    'SedModel',
    'BaseModel',
    'TimeCourseProcessConfigSchema',
    'ModelParameter',
    'ProcessConfig',
    'Port',
    'State'
]


# TODO: Parse this into sep. library datamodels


# --- MODEL ATTRIBUTES
class BaseModel(_BaseModel):
    """Custom implementation of `pydantic.BaseModel` that allows for arbitrary types in the data model.

        TODO: add `protected_namespaces`
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, protected_namespaces=())


class ModelParameter(BaseModel):
    name: str
    feature: str
    value: Union[float, int, str]
    scope: str


class SpeciesChanges(BaseModel):  # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
    name: str
    unit: Union[str, NoneType, ModelParameter] = Field(default='')
    initial_concentration: Optional[Union[float, ModelParameter]] = None
    initial_particle_number: Optional[Union[float, NoneType, ModelParameter]] = None
    initial_expression: Union[str, NoneType, ModelParameter] = Field(default='')
    expression: Union[str, NoneType, ModelParameter] = Field(default='')


class GlobalParameterChanges(BaseModel):  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
    name: str
    initial_value: Union[float, NoneType] = Field(default=None)
    initial_expression: Union[str, NoneType] = Field(default=None)
    expression: Union[str, NoneType] = Field(default=None)
    status: Union[str, NoneType] = Field(default=None)
    param_type: Union[str, NoneType] = Field(default=None)  # ie: fixed, assignment, reactions, etc


class ReactionParameter(BaseModel):
    parameter_name: str
    value: Union[float, int, str]


class ReactionChanges(BaseModel):
    """
        Parameters:
            reaction_name:`str`: name of the reaction you wish to change.
            parameter_changes:`List[ReactionParameter]`: list of parameters you want to change from
                `reaction_name`. Defaults to `[]`, which denotes no parameter changes.

    """
    reaction_name: str
    parameter_changes: List[ReactionParameter] = Field(default=[])
    reaction_scheme: Union[NoneType, str] = Field(default=None)


class TimeCourseModelChanges(BaseModel):
    species_changes: List[SpeciesChanges] = Field(default=[])
    global_parameter_changes: List[GlobalParameterChanges] = Field(default=[])
    reaction_changes: List[ReactionChanges] = Field(default=[])


class ModelSource(BaseModel):
    value: str


class BiomodelId(ModelSource):
    value: str

    @classmethod
    @field_validator('value')
    def check_value(cls, v):
        assert '/' not in v, "value must not contain a path but rather a valid BioModels id like: 'BIOMODELS...'"
        return v


class ModelFilepath(BaseModel):
    value: str

    @classmethod
    @field_validator('value')
    def check_value(cls, v):
        assert '/' in v, "value must contain a path"
        return v


# --- TIME COURSE MODEL
class TimeCourseModel(BaseModel):
    """The data model declaration for process configuration schemas that support SED.

        Parameters:
            model_id: `str`
            model_source: `Union[biosimulator_processes.data_model.ModelFilepath, biosimulator_processes.data_model.BiomodelId]`
            model_language: `str`
            model_name: `str`
            model_changes: `biosimulator_processes.data_model.TimeCourseModelChanges`
    """
    model_id: str = None
    model_source: Union[str, ModelFilepath, BiomodelId]  # TODO: allow this to be derived from model id <-- SED type validated by constructor
    model_language: Union[str, Dict[str, str]] = Field(default='sbml')
    model_name: Union[str, Dict[str, str]] = Field(default='Unnamed Composite Process TimeCourseModel')
    model_changes: Union[TimeCourseModelChanges, Dict[str, str]] = None
    model_units: Union[Dict[str, str], str] = Field(default='_default')

    @field_validator('model_id')
    def set_id(cls, v):
        if not v:
            print('No v')
            return cls.extract_source()
        else:
            print('yea')
            return v

    @classmethod
    def extract_source(cls):
        if isinstance(cls.model_source, ModelFilepath) or isinstance(cls.model_source, BiomodelId):
            # return cls.model_source.value
            cls.model_id = cls.model_source.value
        elif isinstance(cls.model_source, str):
            # return cls.model_source
            cls.model_id = cls.model_source
        else:
            raise AttributeError('You must pass either a ModelFilepath, BioModelId, or str as model source.')

    @field_validator('model_source')
    @classmethod
    def set_source(cls, v: str):
        """Verify that the model source is set to only either a path or a biomodels id"""
        # if '/' in cls.model_source:
        #     return ModelFilepath(value=cls.model_source)
        # elif 'BIO' in cls.input_source:
        #     return BiomodelId(value=cls.model_source)
        if '/' in v:
            return ModelFilepath(value=v)
        elif 'BIO' in v:
            return BiomodelId(value=v)
        elif isinstance(v, ModelFilepath):
            return v
        # else:
        #     raise AttributeError('You must pass either a model filepath or valid biomodel id.')


# --- PORTS
class PortSchema(BaseModel):
    input_value_names: List[str]  # user input
    _schema: Dict[str, List[str]]

    @classmethod
    @field_validator('_schema')
    def set_value(cls):
        return {
            input_value: [f'{input_value}_store']
            for input_value in cls.input_value_names}


# --- EMITTERS
class EmittedType(BaseModel):
    value_name: str
    _type: str  # ie: 'tree[float]'


class EmitterConfig(BaseModel):
    name: str
    emit: Union[List[EmittedType], Dict[str, str]]  # ie: {'floating_species': 'tree[float]'},


class EmitterInstance:
    _type: str = Field(default='step')
    address: str = Field(default='local:ram-emitter')
    emit_types: List[EmittedType]
    config: Dict[str, Dict[str, str]]
    inputs: PortSchema  # these names might be the same as self.config

    @classmethod
    @field_validator('config')
    def set_value(cls):
        config = {
            'emit': {
                emit_type.value_name: emit_type._type
                for emit_type in cls.emit_types
            }
        }


# --- TYPE REGISTRY
class ProcessConfig(BaseModel):
    value: Dict


class Port(BaseModel):
    value: Dict


class State(BaseModel):
    _type: str
    address: str
    config: ProcessConfig
    inputs: Port
    outputs: Port


# --- PROCESSES
class ProcessConfigSchema(BaseModel):
    config: Dict = Field(default={})


class ProcessConfig(BaseModel):
    process_name: str


class CopasiProcessConfig(ProcessConfig):
    method: str = Field(default='deterministic')
    model: TimeCourseModel

    # @field_serializer('model', when_used='json')
    # @classmethod
    # def serialize_model(cls, model):
    #     return model.model_dump_json()

    def get_config(self):
        """TODO: make deep copy before pop"""
        config = self.model_dump()
        config.pop('process_name')
        return config

    # @field_validator('model')
    # @classmethod
    # def validate_model_source(cls, v):
    #     if isinstance(cls.model, TimeCourseModel):
    #         if not v.model_source.value:
    #             raise AttributeError('You must pass a valid model source type: either a model filepath or valid biomodel id')
    #         else:
    #             return v


class ProcessInstance(BaseModel):
    _type: str
    address: str
    config: Union[CopasiProcessConfig, ProcessConfigSchema]
    inputs: PortSchema
    outputs: PortSchema

    @classmethod
    @field_validator('address')
    def check_value(cls, v):
        pass


# --- PROCESS CONFIG SCHEMAS
class TimeCourseModelSchema(BaseModel):
    model_id: str = 'string'
    model_source: str = 'tree[string]'
    model_language: Dict[str, str] = {
        '_type': 'string',
        '_default': 'sbml'}
    model_name: Dict[str, str] = {
        '_type': 'string',
        '_default': 'composite_process_model'}
    model_changes: Dict[str, str] = {
        'species_changes': 'maybe[tree[string]]',
        'global_parameter_changes': 'maybe[tree[string]]',
        'reaction_changes': 'maybe[tree[string]]'}
    model_units: str = 'maybe[tree[string]]'



class TimeCourseProcessConfigSchema(BaseModel):
    model: TimeCourseModelSchema = TimeCourseModelSchema()
    method: Dict[str, str] = {
        '_type': 'string',
        '_default': 'deterministic'}


# --- INSTALLATION
class DependencyFile(BaseModel):
    name: str
    hash: str


class InstallationDependency(BaseModel):
    name: str
    version: str
    markers: str = Field(default='')  # ie: "markers": "platform_system == \"Windows\""
    files: List[DependencyFile] = Field(default=[])


class Simulator(BaseModel):
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
        'model_source': 'tree[string]',  # 'string',    # could be used as the "model_file" or "biomodel_id" below (SEDML l1V4 uses URIs); what if it was 'model_source': 'sbml:model_filepath'  ?
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
