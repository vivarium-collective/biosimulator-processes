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
from process_bigraph import Process, ProcessTypes

from bsp.utils.membrane_utils import extract_data, parse_ply, calculate_preferred_area, new_parameters


class SimpleMembraneProcess(Process):
    config_schema = {
        'mesh_file': 'MeshFileConfig',
        'geometry': 'GeometryConfig',
        'tension_model': 'TensionModelConfig',
        'osmotic_model': 'OsmoticModelConfig',
        'parameters': 'ParametersConfig',
        'save_period': 'integer',
        'tolerance': 'float',
        'characteristic_time_step': 'integer',
        'total_time': 'integer'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)

        # set simulation params
        self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
        self.total_time = self.config.get("total_time", 1000)
        self.tension_modulus = self.config["tension_model"].get("modulus", 0.1)

        # parse input of either mesh file or geometry spec
        mesh_file = self.config.get("mesh_file")
        if mesh_file:
            self.initial_faces, self.initial_vertices = parse_ply(mesh_file)
        else:
            geometry = self.config.get("geometry")
            shape = geometry['type']
            mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
            self.initial_faces, self.initial_vertices = mesh_constructor(**geometry['parameters'])

        self.param_spec = self.config.get("parameters")

        # TODO: should this be dynamic?
        # self.default_osmotic_strength = self.config["osmotic_model"]["strength"]

        # set initial params
        # self.parameters = dg.Parameters()
        # if init_param_spec:
        #     for attribute_name, attribute_spec in init_param_spec.items():  # ie: adsorption, aggregation, bending, etc
        #         attribute = getattr(self.parameters, attribute_name)
        #         for name, value in attribute_spec.items():
        #             setattr(attribute, name, value)

    def initial_state(self):
        # TODO: get initial parameters, return type??
        initial_geometry = {
                "faces": self.initial_faces.tolist(),
                "vertices": self.initial_vertices.tolist(),
        }
        initial_velocities = [[0.0, 0.0, 0.0] for _ in self.initial_vertices]
        return {
            "geometry": initial_geometry,
            "velocities": initial_velocities
        }

    def inputs(self):
        """
        - The first three types are used to parameterize the kth Geometry
        - The preferred_volume, current_volume, and osmotic_strength is used to parameterize the kth Osmotic pressure model.
        - The tension model is parameterized by inference into the osmotic model. The modulus is static.
        """
        return {
            'geometry': 'GeometryType',
            'protein_density': 'ProteinDensityType',
            'velocities': 'VelocitiesType',
            'external_force': 'ExternalForceType',
            'osmotic_parameters': 'OsmoticParametersType'
            # 'preferred_volume': 'float',
            # 'current_volume': 'float',
            # 'osmotic_strength': 'float',
        }

    def outputs(self):
        return {
            'geometry': 'GeometryType',  # {faces: [[]], vertices: [[]]}
            'protein_density': 'ProteinDensityType',
            'velocities': 'VelocitiesType',
            'external_force': 'ExternalForceType',
            'osmotic_parameters': 'OsmoticParametersType'
            # 'preferred_volume': 'float',
            # 'current_volume': 'float',
            # 'osmotic_strength': 'float',
        }

    def update(self, state, interval):
        # parameterize kth geometry from k-1th outputs
        previous_geometry = state.get("geometry")
        input_faces = previous_geometry["faces"]
        input_vertices = previous_geometry["vertices"]
        previous_faces = np.array(input_faces) if isinstance(input_faces, list) else input_faces
        previous_vertices = np.array(input_vertices) if isinstance(input_vertices, list) else input_vertices
        geometry_k = dg.Geometry(previous_faces, previous_vertices)

        # set the kth osmotic volume model  # dfba vals here in update
        osmotic_params_k = state["osmotic_parameters"]
        osmotic_model_k = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=osmotic_params_k["preferred_volume"],  # make input port here if value has changed (fba)
            reservoirVolume=osmotic_params_k["reservoir_volume"],  # output port
            strength=osmotic_params_k["strength"],
            volume=osmotic_params_k["current_volume"]  # TODO: should we add this?
        )

        # set the surface area tension model
        preferred_area = calculate_preferred_area(osmotic_params=osmotic_params_k)
        tension_model_k = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.tension_modulus,
            preferredArea=preferred_area,
        )

        # instantiate kth params
        parameters_k = new_parameters(self.param_spec)
        parameters_k.tension.form = tension_model_k
        parameters_k.osmotic.form = osmotic_model_k

        # instantiate and initialize kth system using Geometry, proteinDensity, velocity, and parameters
        previous_protein_density = state["protein_density"]
        previous_velocities = state["velocities"]
        system_k = dg.System(
            geometry=geometry_k,
            proteinDensity=previous_protein_density,
            velocity=previous_velocities,
            parameters=parameters_k
        )
        system_k.initialize()

        # set up solver and parse time params
        output_dir_k = Path(tmp.mkdtemp())
        # interval_step = self.characteristic_time_step * self.save_period
        # total_time_k = (interval + 1) * interval_step
        fe = dg.Euler(
            system=system_k,
            characteristicTimeStep=self.characteristic_time_step,
            savePeriod=self.save_period,
            totalTime=interval,
            tolerance=self.tolerance,
            outputDirectory=str(output_dir_k)
        )
        fe.ifPrintToConsole = True
        fe.ifOutputTrajFile = True

        # # run solver and extract data
        success = fe.integrate()  # or should this be fe.step(interval)?
        output_path_k = str(output_dir_k / "traj.nc")
        data = Dataset(output_path_k, 'r')
        variables['proteindensity'][:][0].shape, variables['velocities'][:][0].shape, variables['externalForce'][:]
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
