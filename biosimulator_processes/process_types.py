"""The following types have been derived from both SEDML L1v4 and basico itself.

        BASICO_MODEL_CHANGES_TYPE = {
            'species_changes': {   # <-- this is done like set_species('B', kwarg=) where the inner most keys are the kwargs
                'species_name': {
                    'unit': 'maybe[string]',
                    'initial_concentration': 'maybe[float]',
                    'initial_particle_number': 'maybe[float]',
                    'initial_expression': 'maybe[string]',
                    'expression': 'maybe[string]'
                }
            },
            'global_parameter_changes': {   # <-- this is done with set_parameters(PARAM, kwarg=). where the inner most keys are the kwargs
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
    'model_id': 'string',    # could be used as the BioModels id
    'model_source': 'string',    # could be used as the "model_file" below (SEDML l1V4 uses URIs); what if it was 'model_source': 'sbml:model_filepath'  ?
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
    }
}


# ^ Here, the model changes would be applied in either two ways:
#  A. (model_file/biomodel_id is passed): after model instatiation in the constructor
#  B. (no model_file or biomodel_id is passed): used to extract reactions. Since adding reactions to an empty model technically
#   is an act of "changing" the model (empty -> context), it is safe to say that you must pass 'model': {'model_changes': etc...} instead.
