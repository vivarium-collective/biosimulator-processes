from typing import Dict, List, Union, Tuple, Optional
from types import NoneType
from abc import ABC, abstractmethod
from pydantic import BaseModel as Base, field_validator, field_serializer, Field, ConfigDict


__all__ = [
    'SpeciesChanges',
    'GlobalParameterChanges',
    'ReactionParameter',
    'ReactionChanges',
    'ModelChanges',
    'ModelSource',
    'BiomodelId',
    'ModelFilepath',
    'Model',
    'ProcessConfigSchema',
    'CopasiProcessConfigSchema',
    'PortSchema',
    'EmittedType',
    'EmitterInstance',
    'ProcessInstance',
    'FromDict',
    'BasicoModelChanges',
    'SedModel'
]


# TODO: You may be able to resolve this warning by setting `model_config['protected_namespaces'] = ()`.
class BaseModel(Base):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    # protected_namespaces: Tuple = Field(default=())


class SpeciesChanges(BaseModel):  # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
    name: str
    unit: Union[str, NoneType] = Field(default='')
    initial_concentration: Optional[float] = None
    initial_particle_number: Optional[Union[float, NoneType]] = None
    initial_expression: Union[str, NoneType] = Field(default='')
    expression: Union[str, NoneType] = Field(default='')


class GlobalParameterChanges(BaseModel):  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
    parameter_name: str
    initial_value: Union[float, NoneType] = Field(default=None)
    initial_expression: Union[str, NoneType] = Field(default=None)
    expression: Union[str, NoneType] = Field(default=None)
    status: Union[str, NoneType] = Field(default=None)
    param_type: Union[str, NoneType] = Field(default=None)  # ie: fixed, assignment, reactions, etc


class ReactionParameter(BaseModel):
    parameter_name: str
    value: Union[float, int, str]


class ReactionChanges(BaseModel):
    reaction_name: str
    reaction_parameters: Union[NoneType, Dict[str, ReactionParameter]] = Field(default=None)
    reaction_scheme: Union[NoneType, str] = Field(default=None)


class ModelChanges(BaseModel):
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


class Model(BaseModel):
    """The data model declaration for process configuration schemas that support SED.

        Parameters:
            model_id: `str`
            model_source: `Union[biosimulator_processes.data_model.ModelFilepath, biosimulator_processes.data_model.BiomodelId]`
            model_language: `str`
            model_name: `str`
            model_changes: `biosimulator_processes.data_model.ModelChanges`
    """
    model_id: str = Field(default='')
    model_source: Union[str, ModelFilepath, BiomodelId]  # <-- SED type validated by constructor
    model_language: str = Field(default='sbml')
    model_name: str = Field(default='Unnamed Composite Process Model')
    model_changes: ModelChanges
    model_units: Union[Dict[str, str], None] = None

    @field_validator('model_source')
    @classmethod
    def set_value(cls, v: str):
        """Verify that the model source is set to only either a path or a biomodels id"""
        # if '/' in cls.model_source:
        #     return ModelFilepath(value=cls.model_source)
        # elif 'BIO' in cls.input_source:
        #     return BiomodelId(value=cls.model_source)
        if '/' in v:
            return ModelFilepath(value=v)
        elif 'BIO' in v:
            return BiomodelId(value=v)
        else:
            raise AttributeError('You must pass either a model filepath or valid biomodel id.')


class ProcessConfigSchema(BaseModel):
    config: Dict = Field(default={})


class CopasiProcessConfigSchema(BaseModel):
    process_name: Optional[Union[str, NoneType]] = None
    method: str = Field(default='deterministic')
    model: Union[Model, Dict]

    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.model, Model):
            self.model = self.model.model_dump()

    @classmethod
    @field_serializer('model')
    def serialize_model(cls):
        return cls.model.model_dump()

    def get_config(self):
        config = self.model_dump()
        config.pop('process_name')
        return config

    '''@classmethod
    @field_validator('model')
    def set_model(cls):
        if isinstance(cls.model, Model):
            return cls.model.model_dump()'''


class PortSchema(BaseModel):
    input_value_names: List[str]  # user input
    _schema: Dict[str, List[str]]

    @classmethod
    @field_validator('_schema')
    def set_value(cls):
        return {
            input_value: [f'{input_value}_store']
            for input_value in cls.input_value_names}


class EmittedType:
    value_name: str
    _type: str  # ie: 'tree[float]'


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


class ProcessInstance:
    _type: str
    address: str
    config: Union[CopasiProcessConfigSchema, ProcessConfigSchema]
    inputs: PortSchema
    outputs: PortSchema
    emitter: Union[EmitterInstance, NoneType] = Field(default=None)

    @classmethod
    @field_validator('address')
    def check_value(cls, v):
        pass


# Non-Pydantic FromDict classes
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
    # The first 3 params are NOT optional below for a Model in SEDML. model_source has been adapted to mean point of residence
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