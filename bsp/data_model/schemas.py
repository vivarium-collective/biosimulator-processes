"""
Type schema definitions relating to process implementations within this application.

The type name suffix is used to denote its function. Currently there are two suffixes:

- ...Type -> this relates to the schema for input and output port data only
- ...Config -> this relates to the schema for configuration data only (constructor)
"""


__all__ = [
    'BoundsType',
    'PositiveFloatType',
    'ExternalForcesType',
    'ProteinDensityType',
    'GeometryType',
    'VelocitiesType',
    'OsmoticParametersType',
    'OsmoticModelConfig',
    'SBMLFileCobraConfig',
    'SBMLModelChangesConfig',
    'SBMLModelConfig',
    'TimeCourseConfig',
    'TensionModelConfig'
]


# create new types
def apply_non_negative(schema, current, update, core):
    new_value = current + update
    return max(0, new_value)


def check_sbml(state, schema, core):
    import cobra
    # Do something to check that the value is a valid SBML file
    valid = cobra.io.sbml.validate_sbml_model(state)  # TODO -- this requires XML
    # valid = cobra.io.load_json_model(value)
    if valid:
        return True
    else:
        return False


def check_mesh_file(state, schema, core):
    # TODO: check the state for .ply extension in filepath within config
    pass


# -- types: that is, schemas related to input and output port data, not configs

PositiveFloatType = {
    '_type': 'positive_float',
    '_inherit': 'float',
    '_apply': apply_non_negative
}

BoundsType = {
    'lower': 'maybe[float]',
    'upper': 'maybe[float]'
}

ExternalForcesType = {
    '_inherit': 'list'
}

GeometryType = {
    "faces": 'list',  # "list[list[integer]]",
    "vertices": 'list'  # "list[list[float]]",
}

OsmoticParametersType = {
    'preferred_volume': 'float',
    'volume': 'maybe[float]',  # current (actual) volume by which a potential is created when compared to preferred volume
    'strength': 'float',
    'reservoir_volume': 'float'  # represents the environment outside the membrane, which can exchange solutes or exert osmotic pressure on the system
}

ProteinDensityType = 'list[float]'

VelocitiesType = 'list[float]'


# -- configs: that is, schemas related to config_schema specs only --

DatabaseConfig = {
    'connection_uri': 'string',
    'experiment_id': 'maybe[string]',
    'emit_limit': 'integer',
    'database': 'maybe[string]',
}

GeometryConfig = {
    'type': 'string',  # if used, ie; 'icosphere'
    'parameters': 'tree'  # params required for aforementioned shape type
}

MeshFileConfig = {
    '_inherit': 'string',
    '_check': check_mesh_file
}

# TODO: fully implement this with all attributes
ParametersConfig = 'tree'

SBMLFileCobraConfig = {
    '_inherit': 'string',
    # '_check': check_sbml,
    '_apply': 'set',
}

SBMLModelChangesConfig = {
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

SBMLModelConfig = {
    'model_id': 'string',
    'model_source': 'string',
    'model_language': {
        '_default': 'string',
        '_type': 'string'
    },
    'model_name': 'string',
    'model_units': 'tree[string]',
    'model_changes': SBMLModelChangesConfig  # 'tree[string]'
}

TimeCourseConfig = {
    'model': SBMLModelConfig,
    'time_config': 'tree[string]',  # ie: {start, stop, steps}
    'species_context': {
        '_default': 'concentrations',
        '_type': 'string'
    },
    'working_dir': 'string'
}

TensionModelConfig = {
    'modulus': 'float',
    'preferredArea': 'float'
}

OsmoticModelConfig = {
    'volume': 'float',
    'preferred_volume': 'float',
    'reservoir_volume': 'float',
    'strength': 'float'  # what units is this in??
}



