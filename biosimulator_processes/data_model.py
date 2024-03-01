from pydantic import BaseModel
from typing import *
from abc import ABC, abstractmethod


'''class ModelChange(BaseModel):
    config: Union[Dict[str, Dict[str, Dict[str, Union[float, str]]]], Dict[str, Dict[str, Union[Dict[str, float], str]]]]


class ModelChanges(BaseModel):
    species_changes: ModelChange = None
    global_parameter_changes: ModelChange = None
    reaction_changes: ModelChange = None


class ModelSource(ABC):
    value: str

    def __init__(self):
        super().__init__()

    @abstractmethod
    def check_value(self):
        pass


class BiomodelId(ModelSource, BaseModel):
    value: str

    def __init__(self):
        super().__init__()
        self.check_value()

    def check_value(self):
        assert '/' not in self.value


class ModelFilepath(BaseModel):
    value: str
    
    def __init__(self):
        super().__init__()
        self.check_value()

    def check_value(self):
        assert '/' in self.value
    

class SedModel(BaseModel):
    model_id: Optional[str] = None
    model_source: str
    model_language: str = 'sbml'
    model_name: str = 'composite_process_model'
    model_changes: ModelChanges'''


changes = {
    'species_changes': {
        'A': {
            'initial_concent': 24.2,
            'b': 'sbml'
        }
    }
}

r = {
    'reaction_name': {
        'parameters': {
            'reaction_parameter_name': 23.2  # (new reaction_parameter_name value)  <-- this is done with set_reaction_parameters(name="(REACTION_NAME).REACTION_NAME_PARAM", value=VALUE)
        },
        'reaction_scheme': 'maybe[string]'   # <-- this is done like set_reaction(name = 'R1', scheme = 'S + E + F = ES')
    }
}


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
    name: str
    value: Union[float, int, str]


class ReactionChanges(BaseModel):
    reaction_name: str
    reaction_parameters: Dict[str, ReactionParameter]
    reaction_scheme: str


class ModelChanges:
    pass



CHANGES_SCHEMA = """The following types have been derived from both SEDML L1v4 and basico itself.

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
