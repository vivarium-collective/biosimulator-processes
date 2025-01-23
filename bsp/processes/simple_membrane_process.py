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

from bsp.utils.membrane_utils import extract_data, parse_ply, calculate_preferred_area, new_parameters, extract_last_data


class SimpleMembraneProcess(Process):
    config_schema = {
        'mesh_file': 'MeshFileConfig',
        'geometry': 'GeometryConfig',
        'tension_model': 'TensionModelConfig',
        'osmotic_model': 'OsmoticModelConfig',
        'parameters': 'ParametersConfig',
        'save_period': 'integer',
        'tolerance': 'float',
        'characteristic_time_step': 'integer'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)

        # set simulation params
        self.save_period = self.config.get("save_period", 1)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 1e-8)
        self.tension_modulus = self.config["tension_model"].get("modulus", 0.1)

        # parse input of either mesh file or geometry spec
        mesh_file = self.config.get("mesh_file")
        if mesh_file:
            self.initial_geometry = dg.Geometry(mesh_file)
            self.initial_faces = self.initial_geometry.getFaceMatrix()
            self.initial_vertices = self.initial_geometry.getVertexMatrix()
        else:
            geometry = self.config.get("geometry")
            shape = geometry['type']
            mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
            self.initial_faces, self.initial_vertices = mesh_constructor(**geometry['parameters'])

        # get parameters, osmotic, and tension params from config
        self.param_spec = self.config.get("parameters")
        self.parameters = new_parameters(self.param_spec)
        self.osmotic_model_spec = self.config.get("osmotic_model")
        self.tension_model_spec = self.config.get("tension_model")

        # this geometry is initially parameterized by the geometry spec, but remains stateful as it mutates during update calls
        self.geometry = dg.Geometry(self.initial_faces, self.initial_vertices)

    def initial_state(self):
        initial_geometry = {
            "faces": self.initial_faces.tolist(),
            "vertices": self.initial_vertices.tolist(),
        }

        # set initial velocities to an array of the correct shape to 0.0, 0.0, 0.0 TODO: should this be different?
        initial_velocities = np.zeros(self.initial_vertices.shape).tolist()

        # set initial protein density (gradient) to constant (1.) for all vertices
        initial_protein_density = np.ones(self.initial_vertices.shape[0]).tolist()

        # set initial volume and surface area from config
        initial_volume = self.osmotic_model_spec["volume"]
        initial_preferred_volume = self.osmotic_model_spec["preferred_volume"]
        initial_res_volume = self.osmotic_model_spec["reservoir_volume"]
        initial_surface_area = self.geometry.getSurfaceArea()

        # similarly set no forces as initial output
        initial_net_forces = np.zeros(self.initial_vertices.shape).tolist()

        return {
            "geometry": initial_geometry,
            "velocities": initial_velocities,
            "protein_density": initial_protein_density,
            "volume": initial_volume,
            "preferred_volume": initial_preferred_volume,
            "reservoir_volume": initial_res_volume,
            "surface_area": initial_surface_area,
            "net_forces": initial_net_forces,
        }

    def inputs(self):
        """
        - The first three types are used to parameterize the kth Geometry
        - The preferred_volume, current_volume, and osmotic_strength is used to parameterize the kth Osmotic pressure model.
        - The tension model is parameterized by inference into the osmotic model. The modulus is static.
        """
        return {
            'geometry': 'GeometryType',  # 'tree',
            'protein_density': 'ProteinDensityType',  # 'list',
            'velocities': 'VelocitiesType',  # 'list',
            'volume': 'float',
            'preferred_volume': 'float',
            'reservoir_volume': 'float',
            'surface_area': 'float',
            'osmotic_strength': 'float',
        }

    def outputs(self):
        return {
            'geometry': 'GeometryType',
            'protein_density': 'ProteinDensityType',
            'velocities': 'VelocitiesType',
            'volume': 'float',
            'preferred_volume': 'float',
            'reservoir_volume': 'float',
            'surface_area': 'float',
            'net_forces': 'MechanicalForcesType'
        }

    def update(self, state, interval):
        # parameterize kth geometry from k-1th outputs
        input_geometry = state.get("geometry")
        input_faces = input_geometry["faces"]
        input_vertices = input_geometry["vertices"]
        previous_faces = np.array(input_faces) if isinstance(input_faces, list) else input_faces
        previous_vertices = np.array(input_vertices) if isinstance(input_vertices, list) else input_vertices
        # previous_geometry = dg.Geometry(previous_faces, previous_vertices)
        self.geometry.setInputVertexPositions(previous_vertices)

        # set the kth osmotic volume model  # dfba vals here in update
        preferred_volume_k = state["preferred_volume"]  # TODO: should this be constant/static?
        volume_k = state["volume"]
        reservoir_volume_k = state["reservoir_volume"]
        osmotic_strength_k = state.get("osmotic_strength", self.osmotic_model_spec["strength"])
        osmotic_model_k = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=preferred_volume_k,  # make input port here if value has changed (fba)
            reservoirVolume=reservoir_volume_k,  # output port
            strength=osmotic_strength_k,
            # volume=volume_k  # output port
        )

        # set the surface area tension model
        preferred_area_k = calculate_preferred_area(v_preferred=preferred_volume_k)
        area_k = state["surface_area"]
        tension_model_k = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.tension_modulus,
            preferredArea=preferred_area_k,
            # area=area_k,
        )

        # update the tension and osmotic params
        self.parameters.tension.form = tension_model_k
        self.parameters.osmotic.form = osmotic_model_k

        # instantiate and initialize kth system using Geometry, proteinDensity, velocity, and parameters
        protein_density_k = np.array(state["protein_density"])
        velocities_k = np.array(state["velocities"])

        # we parameterize the kth system with the stateful geometry that has been updated with the latest vertex coordinates
        system_k = dg.System(
            geometry=self.geometry,
            proteinDensity=protein_density_k,
            velocity=velocities_k,
            parameters=self.parameters
        )
        system_k.initialize()

        # set up solver and parse time params
        output_dir_k = Path(tmp.mkdtemp())
        integrator_k = dg.Euler(
            system=system_k,
            characteristicTimeStep=self.characteristic_time_step,
            savePeriod=self.save_period,
            totalTime=1,  # is this what we want: atomic time step or should this be related to the interval? Isn't dt always 1 anyway in this context?
            tolerance=self.tolerance,
            outputDirectory=str(output_dir_k)
        )
        integrator_k.ifPrintToConsole = True
        integrator_k.ifOutputTrajFile = True

        # run integration
        success = integrator_k.integrate()  # or should this be integrator_k.step(interval)?

        # uncomment and implement below for IO style update
        # output_path_k = str(output_dir_k / "traj.nc")
        # data = Dataset(output_path_k, 'r')

        # get kth protein densities from kth system
        output_protein_density = system_k.getProteinDensity().tolist()

        # get kth velocities from kth system
        output_velocities = system_k.getVelocity().tolist()

        # verify geometry instance by getting it from the system (in case it has mutated). TODO: is this needed?
        geo = system_k.getGeometry()
        output_geometry = {
            "faces": geo.getFaceMatrix().tolist(),
            "vertices": geo.getVertexMatrix().tolist(),
        }

        # get kth volume and surface area from output geometry
        vol_variation_vectors = geo.getVertexVolumeVariationVectors()  # TODO: this is not yet used
        output_volume = geo.getVolume()
        output_surface_area = geo.getSurfaceArea()

        # get kth mechanical force vectors (that is, the net sum of x, y, and z vectors for each vertex)
        forces_k = system_k.getForces()
        output_force_vectors = forces_k.getMechanicalForceVec().tolist()

        # clean up temporary files
        shutil.rmtree(str(output_dir_k))

        return {
            'geometry': output_geometry,
            'protein_density': output_protein_density,
            'velocities': output_velocities,
            'volume': output_volume,
            'preferred_volume': preferred_volume_k,
            'reservoir_volume': reservoir_volume_k,
            'surface_area': output_surface_area,
            'net_forces': output_force_vectors
        }


# velocities_k = extract_last_data(dataset=data, data_name="velocities")
# faces_k = geometry_k.getFaceMatrix().tolist()
# vertices_k = geometry_k.getVertexMatrix().tolist()
# protein_density_k = extract_last_data(dataset=data, data_name="proteindensity")
# external_force_k = extract_last_data(dataset=data, data_name="externalForce")
# class SimpleMembraneProcess(Process):
#     config_schema = {
#         'mesh_file': 'MeshFileConfig',
#         'geometry': 'GeometryConfig',
#         'tension_model': 'TensionModelConfig',
#         'osmotic_model': 'OsmoticModelConfig',
#         'parameters': 'ParametersConfig',
#         'save_period': 'integer',
#         'tolerance': 'float',
#         'characteristic_time_step': 'integer',
#         'total_time': 'integer'
#     }
#
#     def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
#         super().__init__(config, core)
#
#         # set simulation params
#         self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
#         self.tolerance = self.config.get("tolerance", 1e-11)
#         self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
#         self.total_time = self.config.get("total_time", 1000)
#         self.tension_modulus = self.config["tension_model"].get("modulus", 0.1)
#
#         # parse input of either mesh file or geometry spec
#         mesh_file = self.config.get("mesh_file")
#         if mesh_file:
#             self.initial_geometry = dg.Geometry(mesh_file)
#             self.initial_faces = self.initial_geometry.getFaceMatrix()
#             self.initial_vertices = self.initial_geometry.getVertexMatrix()
#         else:
#             geometry = self.config.get("geometry")
#             shape = geometry['type']
#             mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
#             self.initial_faces, self.initial_vertices = mesh_constructor(**geometry['parameters'])
#
#         # get parameters, osmotic, and tension params from config
#         self.param_spec = self.config.get("parameters")
#         self.osmotic_model_spec = self.config.get("osmotic_model")
#         self.tension_model_spec = self.config.get("tension_model")
#
#     def initial_state(self):
#         initial_geometry = {
#             "faces": self.initial_faces.tolist(),
#             "vertices": self.initial_vertices.tolist(),
#         }
#
#         initial_velocities = []
#         initial_protein_density = []
#         for vertex in self.initial_vertices:
#             # set empty velocities TODO: can this work?
#             for _ in range(3):
#                 initial_velocities.append(0.0)
#             # set constant protein density TODO: make this more dynamic.
#             initial_protein_density.append(1.)
#
#         initial_osmotic_params = {
#             "preferred_volume": self.osmotic_model_spec["preferred_volume"],
#             "volume": self.osmotic_model_spec["volume"],
#             "strength": self.osmotic_model_spec["strength"],
#             "reservoir_volume": self.osmotic_model_spec["reservoir_volume"]
#         }
#
#         return {
#             "geometry": initial_geometry,
#             "velocities": initial_velocities,
#             "external_force": [],
#             "osmotic_parameters": initial_osmotic_params,
#             "protein_density": initial_protein_density
#         }
#
#     def inputs(self):
#         """
#         - The first three types are used to parameterize the kth Geometry
#         - The preferred_volume, current_volume, and osmotic_strength is used to parameterize the kth Osmotic pressure model.
#         - The tension model is parameterized by inference into the osmotic model. The modulus is static.
#         """
#         return {
#             'geometry': 'GeometryType',  # 'tree',
#             'protein_density': 'ProteinDensityType',  # 'list',
#             'velocities': 'VelocitiesType',  # 'list',
#             'external_force': 'ExternalForceType',  # 'list',
#             'osmotic_parameters': 'OsmoticParametersType',  # take in osmotic_parameters.preferred_volume from dFBA node
#             'surface_tension_parameters': 'SurfaceTensionParametersType',
#         }
#
#     def outputs(self):
#         return {
#             'geometry': 'GeometryType',  # 'tree',
#             'protein_density': 'ProteinDensityType',  # 'list',
#             'velocities': 'VelocitiesType',  # 'list',
#             'external_force': 'ExternalForceType',  # 'list',
#             'osmotic_parameters': 'OsmoticParametersType',
#             'surface_tension_parameters': 'SurfaceTensionParametersType'
#         }
#
#     def update(self, state, interval):
#         # parameterize kth geometry from k-1th outputs
#         previous_geometry = state.get("geometry")
#         input_faces = previous_geometry["faces"]
#         input_vertices = previous_geometry["vertices"]
#         previous_faces = np.array(input_faces) if isinstance(input_faces, list) else input_faces
#         previous_vertices = np.array(input_vertices) if isinstance(input_vertices, list) else input_vertices
#         geometry_k = dg.Geometry(previous_faces, previous_vertices)
#
#         # set the kth osmotic volume model  # dfba vals here in update
#         previous_osmotic_params = state["osmotic_parameters"]
#         previous_preferred_volume = previous_osmotic_params["preferred_volume"]
#         osmotic_model_k = partial(
#             dgb.preferredVolumeOsmoticPressureModel,
#             preferredVolume=previous_preferred_volume,  # make input port here if value has changed (fba)
#             reservoirVolume=previous_osmotic_params["reservoir_volume"],  # output port
#             strength=previous_osmotic_params["strength"],
#             volume=previous_osmotic_params["volume"]  # output port
#         )
#
#         # set the surface area tension model
#         preferred_area = calculate_preferred_area(v_preferred=previous_preferred_volume)
#         tension_model_k = partial(
#             dgb.preferredAreaSurfaceTensionModel,
#             modulus=self.tension_modulus,
#             preferredArea=preferred_area,
#             area=state['surface_tension_parameters']['area'],
#         )
#
#         # instantiate kth params
#         parameters_k = new_parameters(self.param_spec)
#         parameters_k.tension.form = tension_model_k
#         parameters_k.osmotic.form = osmotic_model_k
#
#         # instantiate and initialize kth system using Geometry, proteinDensity, velocity, and parameters
#         previous_protein_density = np.array(state["protein_density"])
#         previous_velocities = np.array(state["velocities"])
#         system_k = dg.System(
#             geometry=geometry_k,
#             proteinDensity=previous_protein_density,
#             velocity=previous_velocities,
#             parameters=parameters_k
#         )
#         system_k.initialize()
#
#         # set up solver and parse time params
#         output_dir_k = Path(tmp.mkdtemp(dir='membrane_process'))
#         # interval_step = self.characteristic_time_step * self.save_period
#         # total_time_k = (interval + 1) * interval_step
#         fe = dg.Euler(
#             system=system_k,
#             characteristicTimeStep=self.characteristic_time_step,
#             savePeriod=self.save_period,
#             totalTime=interval,
#             tolerance=self.tolerance,
#             outputDirectory=str(output_dir_k)
#         )
#         fe.ifPrintToConsole = True
#         fe.ifOutputTrajFile = True
#
#         # # run solver and extract data
#         success = fe.integrate()  # or should this be fe.step(interval)?
#         output_path_k = str(output_dir_k / "traj.nc")
#         data = Dataset(output_path_k, 'r')
#
#         # get velocities: shape is (t, n_vertices * 3) where t is the number of recorded time points
#         velocities_k = extract_last_data(dataset=data, data_name="velocities")
#
#         # get faces (do we need this?)
#         # faces_k = extract_last_data(dataset=data, data_name="topology")
#         faces_k = geometry_k.getFaceMatrix()
#
#         # get vertices
#         # vertices_k = extract_last_data(dataset=data, data_name="coordinates")
#         vertices_k = geometry_k.getVertexMatrix().tolist()
#
#         # get protein density: shape is (t, n_vertices) so a scalar for each vertex rather than a tuple
#         protein_density_k = extract_last_data(dataset=data, data_name="proteindensity")
#
#         # get external forces TODO: do we need this?
#         external_force_k = extract_last_data(dataset=data, data_name="externalForce")
#
#         # clean up temporary files
#         shutil.rmtree(str(output_dir_k))
#
#         geometry_outputs = {
#             "vertices": vertices_k,
#             "faces": faces_k,
#         }
#
#         return {
#             "geometry": geometry_outputs,
#             "protein_density": protein_density_k,
#             "external_force": external_force_k,
#             "velocities": velocities_k,
#             "osmotic_parameters": osmotic_params_k
#         }
