"""
Membrane process using forward euler gradient descent integration.
"""

import inspect
import os
import shutil
from functools import partial
from pathlib import Path
from typing import Dict, Union, List, Tuple
import tempfile as tmp

import numpy as np
import pymem3dg as dg
import pymem3dg.boilerplate as dgb
from netCDF4 import Dataset
from process_bigraph import Process, ProcessTypes, Composite, pp

from bsp.utils.base_utils import new_document
from bsp.utils.membrane_utils import extract_data, parse_ply


class SimpleMembraneProcess(Process):
    config_schema = {
        'mesh_file': 'string',
        'geometry': {
            'type': 'string',  # if used, ie; 'icosphere'
            'params': 'tree'  # params required for aforementioned shape type
        },
        # 'tension_model': 'tree[float]',
        # 'osmotic_model': 'tree[float]',
        'tension_model': {
            'modulus': 'float',
            'preferredArea': 'float'
        },
        'osmotic_model': {
            'preferredVolume': 'float',
            'reservoirVolume': 'float',
            'strength': 'float'  # what units is this in??
        },
        'parameters': 'tree',
        'save_period': 'integer',
        'tolerance': 'float',
        'characteristic_time_step': 'integer',
        'total_time': 'integer'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)
        # get simulation params
        # self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
        self.total_time = self.config.get("total_time", 100)
        self.total_time = self.config.get("total_time", 1000)

        # parse input of either mesh file or geometry spec
        mesh_file = self.config.get("mesh_file")
        geometry = self.config.get("geometry")

        if mesh_file:
            self.initial_faces, self.initial_vertices = parse_ply(mesh_file)
        else:
            shape = self.config['geometry']['type']
            mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
            self.initial_faces, self.initial_vertices = mesh_constructor(**self.config['geometry']['params'])

        self.default_osmotic_strength = self.config["osmotic_model"]["strength"]

        # set initial params
        self.parameters = dg.Parameters()
        init_param_spec = self.config.get("parameters")
        if init_param_spec:
            for attribute_name, attribute_spec in init_param_spec.items():  # ie: adsorption, aggregation, bending, etc
                attribute = getattr(self.parameters, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)

        self._velocities_type = 'list'  # np.array

    def initial_state(self):
        # TODO: get initial parameters, return type??
        initial_geometry = {
                "faces": self.initial_faces.tolist(),
                "vertices": self.initial_vertices.tolist(),
        }
        initial_velocities = [[0.0, 0.0, 0.0] for _ in self.initial_vertices]
        return {
            "geometry": initial_geometry,
            "velocities": np.array(initial_velocities) if self._velocities_type == 'array' else initial_velocities
        }

    def inputs(self):
        """
        strength: how strongly the system resists deviations from the preferred volume. It is a measure of the system's elasticity or compliance in response to osmotic pressure changes.
        """
        return {
            # 'geometry': 'GeometryType',
            'geometry': {
                'faces': 'tree',
                'vertices': 'tree'
            },
            'protein_densities': 'array',
            'velocities': 'array',
            'preferred_volume': 'float',
        }

    def outputs(self):
        return {
            # 'geometry': 'GeometryType',
            'geometry': {
                'faces': 'tree',
                'vertices': 'tree'
            },
            'protein_densities': 'array',
            'velocities': 'array',
            'reservoir_volume': 'float'
        }

    def update(self, state, interval):
        # take in previous geometry for k
        previous_geometry = state.get("geometry")
        input_faces = previous_geometry["faces"]
        input_vertices = previous_geometry["vertices"]
        previous_faces = np.array(input_faces, dtype=np.uint32) if isinstance(input_faces, list) else input_faces
        previous_vertices = np.array(input_vertices, dtype=np.float64) if isinstance(input_vertices, list) else input_vertices
        geometry_k = dg.Geometry(previous_faces, previous_vertices)

        # set the surface area tension model
        tension_model_k = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.config["tension_model"]["modulus"],
            preferredArea=self.config["tension_model"]["preferredArea"],
        )

        # set the osmotic volume model  # dfba vals here in update
        osmotic_model_k = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=self.config["osmotic_model"]["preferredVolume"],  # make input port here if value has changed (fba)
            reservoirVolume=self.config["osmotic_model"]["reservoirVolume"],  # output port
            strength=self.config["osmotic_model"]["strength"],
        )

        self.parameters.tension.form = tension_model_k
        self.parameters.osmotic.form = osmotic_model_k

        system_k = dg.System(geometry=self.initial_geometry)  # perhaps set velocities here?
        system_k.initialize()



        # set up solver
        output_dir_k = Path(tmp.mkdtemp())
        fe = dg.Euler(
            system=system_k,
            characteristicTimeStep=self.characteristic_time_step,
            savePeriod=self.save_period,
            totalTime=interval,  # interval?
            tolerance=self.tolerance,
            outputDirectory=str(output_dir_k)
        )
        fe.ifPrintToConsole = True
        fe.ifOutputTrajFile = True

        # # run solver and extract data
        success = fe.integrate()  # or should this be fe.step(interval)?
        output_path_k = str(output_dir_k / "traj.nc")
        data = Dataset(output_path_k, 'r')

        # get velocities
        velocities_k = extract_data(dataset=data, data_name="velocities", return_last=True)

        # get faces (do we need this?)
        faces_k = extract_data(dataset=data, data_name="topology", return_last=True)

        # get vertices
        vertices_k = extract_data(dataset=data, data_name="coordinates", return_last=True)

        # parse parameters for iteration
        # param_data_k = parse_parameters(parameters=parameters_k)

        # clean up temporary files
        # shutil.rmtree(str(output_dir_k))

        geometry_out = {
            "vertices": vertices_k,
            "faces": faces_k,
        }

        return {
            "geometry": geometry_out,
            # "parameters": param_data_k,
            "velocities": velocities_k
        }
