from typing import Dict, List, Union
from types import NoneType
from abc import ABC, abstractmethod
from pydantic import BaseModel, field_validator, field_serializer, Field


class SpeciesChanges(BaseModel):  # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
    species_name: str
    unit: str
    initial_concentration: float
    initial_particle_number: float
    initial_expression: str
    expression: str


class GlobalParameterChanges(BaseModel):  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
    parameter_name: str
    initial_value: float
    initial_expression: str
    expression: str
    status: str
    param_type: str  # ie: fixed, assignment, reactions, etc


class ReactionParameter(BaseModel):
    parameter_name: str
    value: Union[float, int, str]


class ReactionChanges(BaseModel):
    reaction_name: str
    reaction_parameters: Dict[str, ReactionParameter]
    reaction_scheme: str


class ModelChanges:
    species_changes: List[SpeciesChanges]
    global_parameter_changes: List[GlobalParameterChanges]
    reaction_changes: List[ReactionChanges]


class ModelSource(ABC, BaseModel):
    value: str = None

    @field_validator('value')
    @abstractmethod
    def check_value(self, v):
        pass


class BiomodelId(ModelSource):
    value: str = None

    @field_validator('value')
    def check_value(self, v):
        assert '/' not in v, "value must not contain a path but rather a valid BioModels id like: 'BIOMODELS...'"
        return v


class ModelFilepath(BaseModel):
    value: str = None

    @field_validator('value')
    def check_value(self, v):
        assert '/' in v, "value must contain a path"
        return v


class Model(BaseModel):
    """The data model declaration for process configuration schemas that support SED"""
    model_id: str = Field(default='')
    input_source: str  # <-- user input
    model_source: Union[ModelFilepath, BiomodelId]  # <-- SED type validated by constructor
    model_language: str = Field(default='sbml')
    model_name: str = Field(default='Unnamed Composite Process Model')
    model_changes: ModelChanges

    @field_validator('model_source')
    def set_value(self):
        """Verify that the model source is set to only either a path or a biomodels id"""
        if '/' in self.input_source:
            return ModelFilepath(value=self.input_source)
        elif 'BIO' in self.input_source:
            return BiomodelId(value=self.input_source)


class ProcessConfigSchema(BaseModel):
    config: Dict


class CopasiProcessConfigSchema(ProcessConfigSchema):
    model: Union[Dict, Model]
    method: str = Field(default='deterministic')


class PortSchema(BaseModel):
    input_value_names: [List[str]]  # user input
    schema: Dict[str, List[str]]

    @field_validator('schema')
    def set_value(self):
        return {
            input_value: [f'{input_value}_store']
            for input_value in self.input_value_names}


class EmittedType:
    value_name: str
    _type: str  # ie: 'tree[float]'


class EmitterInstance:
    _type: str = Field(default='step')
    address: str = Field(default='local:ram-emitter')
    emit_types: List[EmittedType]
    config: Dict[str, Dict[str, str]]
    inputs: PortSchema  # these names might be the same as self.config

    @field_validator('config')
    def set_value(self):
        config = {
            'emit': {
                emit_type.value_name: emit_type._type
                for emit_type in self.emit_types
            }
        }


class ProcessInstance:
    _type: str
    address: str
    config: Union[CopasiProcessConfigSchema, ProcessConfigSchema]
    inputs: PortSchema
    outputs: PortSchema
    emitter: Union[EmitterInstance, NoneType] = Field(default=None)

    @field_validator('address')
    def check_value(self, v):
        pass


# FromDict classes
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
        'model_source': 'string',    # could be used as the "model_file" or "biomodel_id" below (SEDML l1V4 uses URIs); what if it was 'model_source': 'sbml:model_filepath'  ?
        'model_language': {    # could be used to load a different model language supported by COPASI/basico
            '_type': 'string',
            '_default': 'sbml'    # perhaps concatenate this with 'model_source'.value? I.E: 'model_source': 'MODEL_LANGUAGE:MODEL_FILEPATH' <-- this would facilitate verifying correct model fp types.
        },
        'model_name': {
            '_type': 'string',
            '_default': 'composite_process_model'
        },
        'model_changes': {
            'species_changes': 'tree[string]',   # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
            'global_parameter_changes': 'tree[string]',  # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
            'reaction_changes': 'tree[string]'
        },
        'model_units': 'tree[string]'
    }

    def __init__(self, _type: Dict = MODEL_TYPE):
        super().__init__(_type)



