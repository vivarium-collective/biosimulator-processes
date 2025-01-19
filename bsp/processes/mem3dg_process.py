from functools import partial
from pathlib import Path
from typing import Dict, Union

import pymem3dg as dg
import pymem3dg.boilerplate as dgb
from process_bigraph import Process, ProcessTypes


# pymem3dg.boilerplate.preferredAreaSurfaceTensionModel¶
# preferredVolumeOsmoticPressureModel


class MembraneProcess(Process):
    """
    Membrane process consisting of preferredAreaTension and preferredVolumeOsmoticPressure models (expand and contract)

    :config mesh_file: input .ply file TODO: generalize this
    :config tension_model:
    :config osmotic_model:
    :config parameters: dict[str, float]: {**dir(pymem3dg.Parameters()}: 'adsorption', 'aggregation', 'bending', 'boundary', 'damping', 'dirichlet', 'dpd',
        entropy', 'external', 'osmotic', 'point', 'protein', 'proteinMobility', 'selfAvoidance', 'spring', 'temperature', 'tension', 'variation'.

    """
    config_schema = {
        'mesh_file': 'string',
        'tension_model': {
            'modulus': 'float',
            'preferredArea': 'float'
        },
        'osmotic_model': {
            'preferredVolume': 'float',
            'reservoirVolume': 'float',
            'strength': 'float'  # what units is this in??
        },
        'parameters': 'tree[float]'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)

        # create geometry from model file
        self.geometry = dg.Geometry(self.config["mesh_file"])

        # create and set parameters (non pressure model params)
        self.parameters = dg.Parameters()
        param_spec = self.config.get("parameters")
        if param_spec:
            for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregiation, bending, etc
                attribute = getattr(self.parameters, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)

        # set the surface area tension model. TODO: perhaps dynamically unpack?
        self.parameters.tension.form = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.config["tension_model"]["modulus"],
            preferredArea=self.config["tension_model"]["preferredArea"],
        )

        # set the osmotic pressure model
        self.parameters.osmotic.form = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=self.config["osmotic_model"]["preferredVolume"],
            reservoirVolume=self.config["osmotic_model"]["reservoirVolume"],
            strength=self.config["osmotic_model"]["strength"],
        )







