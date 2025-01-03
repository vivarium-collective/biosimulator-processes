"""
Type schema definitions relating to process implementations within this application.
"""


from dataclasses import dataclass, asdict
from typing import Union, Optional, Any, Dict

from bsp.data_model.base import BaseClass

# -- sed-specific type schemas --


@dataclass
class FieldSchema(BaseClass):
    _type: str  # one of the bigraph schema types
    _default: Optional[Any] = None
    # TODO: add more attributes here!

    @property
    def value(self):
        return self._type if self._default is None else self.to_dict()


@dataclass
class SEDModelType(BaseClass):
    model_id: FieldSchema = FieldSchema(_type="string")
    model_source: FieldSchema = FieldSchema(_type="string")
    model_language: FieldSchema = FieldSchema(_type="string", _default="sbml")
    model_name: FieldSchema = FieldSchema(_type="string", _default="composite_process_model")
    model_units: FieldSchema = FieldSchema(_type="tree[string]")
    model_changes: FieldSchema = FieldSchema(_type="tree[string]")

    def to_dict(self):
        return {
            field_name: field_spec.value
            for field_name, field_spec in vars(self).items()
        }


@dataclass
class TimeCourseConfigType(BaseClass):
    model: SEDModelType = SEDModelType()
    time_config: FieldSchema = FieldSchema(_type="tree[string]")
    species_context: FieldSchema = FieldSchema(_type="string", _default="concentrations")
    working_dir: FieldSchema = FieldSchema(_type="string")


# MODEL_TYPE = {
#     'model_id': 'string',
#     'model_source': 'string',  # TODO: add antimony support here.
#     'model_language': {
#         '_type': 'string',
#         '_default': 'sbml'
#     },
#     'model_name': {
#         '_type': 'string',
#         '_default': 'composite_process_model'
#     },
#     'model_units': 'tree[string]',
#     'model_changes': 'tree[string]',
#     # 'model_changes': {
#     #     'species_changes': 'maybe[tree[string]]',
#     #     'global_parameter_changes': 'maybe[tree[string]]',
#     #     'reaction_changes': 'maybe[tree[string]]'
#     # },
#     # 'model_units': 'maybe[tree[string]]'}
# }
# UTC_CONFIG_TYPE = {
#     'model': MODEL_TYPE,  # referenced in registry as 'sed_model'
#     'time_config': 'tree[string]',
#     'species_context': {
#         '_default': 'concentrations',
#         '_type': 'string'
#     },
#     'working_dir': 'string'
# }

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
