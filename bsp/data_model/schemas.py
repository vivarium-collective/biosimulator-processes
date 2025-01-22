"""
Type schema definitions relating to process implementations within this application.
"""


__all__ = [
    'Bounds',
    'PositiveFloat',
    'GeometryType',
    'OsmoticModelType',
    'SedModel',
    'SedModelChanges',
    'SbmlCobra',
    'SedTimeCourseConfig',
    'TensionModelType',
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


# -- sed-specific type schemas --

PositiveFloat = {
    '_type': 'positive_float',
    '_inherit': 'float',
    '_apply': apply_non_negative
}

Bounds = {
    'lower': 'maybe[float]',
    'upper': 'maybe[float]'
}

GeometryParams = {
    "faces": 'list',  # "list[list[integer]]",
    "vertices": 'list'  # "list[list[float]]",
}


GeometryType = GeometryParams


SbmlCobra = {
    '_inherit': 'string',
    # '_check': check_sbml,
    '_apply': 'set',
}

SedModelChanges = {
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

SedModel = {
    'model_id': 'string',
    'model_source': 'string',
    'model_language': {
        '_default': 'string',
        '_type': 'string'
    },
    'model_name': 'string',
    'model_units': 'tree[string]',
    'model_changes': SedModelChanges  # 'tree[string]'
}

SedTimeCourseConfig = {
    'model': SedModel,
    'time_config': 'tree[string]',  # ie: {start, stop, steps}
    'species_context': {
        '_default': 'concentrations',
        '_type': 'string'
    },
    'working_dir': 'string'
}

TensionModelType = {
    'modulus': 'float',
    'preferredArea': 'float'
}

OsmoticModelType = {
    'preferredVolume': 'float',
    'reservoirVolume': 'float',
    'strength': 'float'  # what units is this in??
}

VelocitiesType = {
    '_inherit': 'list'
}

