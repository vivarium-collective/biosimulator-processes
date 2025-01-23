"""
Type schema definitions relating to process implementations within this application.

The type name suffix is used to denote its function. Currently there are two suffixes:

- ...Type -> this relates to the schema for input and output port data only
"""


__all__ = [
    'BoundsType',
    'PositiveFloatType',
    'ExternalForcesType',
    'ProteinDensityType',
    'GeometryType',
    'VelocitiesType',
    'OsmoticParametersType',
    'SurfaceTensionParametersType'
]


# create new types
def apply_non_negative(schema, current, update, core):
    new_value = current + update
    return max(0, new_value)


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

SurfaceTensionParametersType = {
    'area': 'float',  # use Geometry.getArea() for this value
    'modulus': 'float',  # static value (in constructor?)
    'preferred_area': 'float'
}

ProteinDensityType = 'list[float]'

VelocitiesType = 'list[float]'

