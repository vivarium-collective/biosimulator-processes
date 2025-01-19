import inspect
from functools import partial
from pathlib import Path
from typing import Dict, Union
import tempfile as tmp

import pymem3dg as dg
import pymem3dg.boilerplate as dgb
from netCDF4 import Dataset
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
        'parameters': 'tree[float]',
        'save_period': 'integer',
        'tolerance': 'float',
        'characteristic_time_step': 'integer'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)

        # get simulation params
        # that should be given to the composite?:
        # self.total_time = self.config.get("total_time", 10000)
        self.save_period = self.config.get("save_period", 100)
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)

        # create geometry from model file
        self.geometry = dg.Geometry(self.config["mesh_file"])

        # set the surface area tension model. TODO: perhaps dynamically unpack?
        self.tension_model = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.config["tension_model"]["modulus"],
            preferredArea=self.config["tension_model"]["preferredArea"],
        )

        # set the osmotic volume model
        self.osmotic_model = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=self.config["osmotic_model"]["preferredVolume"],
            reservoirVolume=self.config["osmotic_model"]["reservoirVolume"],
            strength=self.config["osmotic_model"]["strength"],
        )

        # set initial params
        self.initial_parameters = dg.Parameters()
        init_param_spec = self.config.get("parameters")
        if init_param_spec:
            for attribute_name, attribute_spec in init_param_spec.items():  # ie: adsorption, aggregiation, bending, etc
                attribute = getattr(self.initial_parameters, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)

    def initial_state(self):
        # TODO: get initial parameters, return type??
        pass

    def inputs(self):
        return {
            "parameters": "tree[float]"
        }

    def outputs(self):
        return {
            "vertices": "list[tuple[float, float, float]]",  # (vx, vy, vz) for v in resulting vertices
            "parameters": "tree[float]"
        }

    def update(self, state, interval):
        # take in parameters k and set them
        parameters_k = dg.Parameters()
        param_spec = state.get("parameters")
        if param_spec:
            for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregiation, bending, etc
                attribute = getattr(parameters_k, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)
        else:
            parameters_k = self.initial_parameters

        # instantiate the params with the class pressure models
        parameters_k.tension.form = self.tension_model
        parameters_k.osmotic.form = self.osmotic_model

        # mk temp dir to parse kth outputs
        system = dg.System(
            geometry=self.geometry,
            parameters=parameters_k
        )

        # set up solver
        output_dir = Path(tmp.mkdtemp())
        fe = dg.Euler(
            system=system,
            characteristicTimeStep=self.characteristic_time_step,
            savePeriod=self.save_period,
            totalTime=interval,  # self.total_time,
            tolerance=self.tolerance,
            outputDirectory=str(output_dir)
        )
        fe.ifPrintToConsole = True
        fe.ifOutputTrajFile = True

        # run solver and extract data
        success = fe.integrate()
        data = Dataset(str(output_dir / "traj.nc"), 'r')
        vertex_data = data.groups['Trajectory'].variables['coordinates'][:]  # x will be divisible by 3 and thus is a time indexed flat list of tuples(xyz) for each vertex in the mesh

        # create array of tuples with vertex data
        vertices = []
        for v_t in vertex_data:
            vertices_t = [(v_t[i], v_t[i+1], v_t[i+2]) for i in range(0, len(v_t), 3)]
            vertices.append(vertices_t)

        # parse parameters for iteration
        param_data = {}
        for param_attr_name in dir(parameters_k):
            if not param_attr_name.startswith("__"):
                param_data[param_attr_name] = {}
                attr = getattr(parameters_k, param_attr_name)
                attr_props = {}
                for inner_name in dir(attr):
                    if not inner_name.startswith("__"):
                        inner_attr = getattr(attr, inner_name)
                        excluded = ["function", "built-in"]
                        if not callable(inner_attr) or not inspect.isbuiltin(inner_attr):
                            attr_props[inner_name] = inner_attr

                param_data[param_attr_name] = attr_props

        return {
            "vertices": vertices,
            "parameters": param_data
        }









