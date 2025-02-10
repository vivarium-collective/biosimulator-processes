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
        'characteristic_time_step': 'integer',
        'console_output': 'boolean',
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core=None):
        super().__init__(config, core)
        # get simulation params
        self.save_period = self.config.get("save_period", 1)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 0.02)
        self.tension_modulus = self.config["tension_model"].get("modulus", 0.1)
        self.console_output = self.config.get("console_output", True)

        # parse input of either mesh file or geometry spec
        initial_faces = None
        initial_vertices = None

        mesh_file = self.config.get("mesh_file")
        if mesh_file:
            geometry = dg.Geometry(mesh_file)
            initial_faces = geometry.getFaceMatrix()
            initial_vertices = geometry.getVertexMatrix()
        else:
            geometry = self.config.get("geometry")
            shape = geometry['type']
            mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
            initial_faces, initial_vertices = mesh_constructor(**geometry['parameters'])

        # this geometry is initially parameterized by the geometry spec, but remains stateful as it mutates during update calls
        self.geometry = dg.Geometry(initial_faces, initial_vertices)
        self.n_vertices = self.geometry.getVertexMatrix().shape[0]

        # get parameters, osmotic, and tension params from config
        self.param_spec = self.config.get("parameters")
        self.parameters = new_parameters(self.param_spec)

        self.system = dg.System(
            geometry=self.geometry,
            parameters=self.parameters,
        )

        self.osmotic_model_spec = self.config.get("osmotic_model")
        self.tension_model_spec = self.config.get("tension_model")
        self.iterations = 0

    def initial_state(self):
        initial_face_matrix = self.geometry.getFaceMatrix().tolist()
        initial_vertices = self.geometry.getVertexMatrix()
        initial_geometry = {
            "faces": initial_face_matrix,
            "vertices": initial_vertices.tolist(),
        }

        # set initial velocities to an array of the correct shape to 0.0, 0.0, 0.0 TODO: should this be different?
        self.system.initialize(True)
        initial_velocities = self.system.getVelocity().tolist()  # np.zeros(initial_vertices.shape).tolist()

        # set initial protein density (gradient) to constant (1.) for all vertices
        initial_protein_density = self.system.getProteinDensity().tolist()  # np.ones(initial_vertices.shape[0]).tolist()

        # set initial volume and surface area from config
        initial_volume = self.osmotic_model_spec["volume"]
        initial_preferred_volume = self.osmotic_model_spec["preferred_volume"]
        initial_res_volume = self.osmotic_model_spec["reservoir_volume"]
        initial_surface_area = self.geometry.getSurfaceArea()

        # similarly set no forces as initial output
        initial_net_forces = np.zeros(initial_vertices.shape).tolist()

        return {
            "geometry": initial_geometry,
            "velocities": initial_velocities,
            "protein_density": initial_protein_density,
            "volume": initial_volume,
            "preferred_volume": initial_preferred_volume,
            "reservoir_volume": initial_res_volume,
            "surface_area": initial_surface_area,
            "net_forces": initial_net_forces,
            "duration": 0.0
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
            'duration': 'integer'
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
            'net_forces': 'MechanicalForcesType',
            'duration': 'integer',
        }

    def update(self, state, interval):
        # parameterize kth geometry from k-1th outputs
        previous_vertices = np.array(state["geometry"]["vertices"][:self.n_vertices])  # TODO: why is -1 in improper format?
        self.geometry.setInputVertexPositions(previous_vertices)

        # set the kth osmotic volume model  # dfba vals here in update
        preferred_volume_k = state["preferred_volume"]  # TODO: should this be constant/static?
        reservoir_volume_k = state["reservoir_volume"]
        osmotic_strength_k = self.osmotic_model_spec["strength"]
        osmotic_model_k = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=preferred_volume_k,  # make input port here if value has changed (fba)
            reservoirVolume=reservoir_volume_k,  # output port
            strength=osmotic_strength_k,
        )

        # set the surface area tension model
        preferred_area_k = calculate_preferred_area(v_preferred=preferred_volume_k)
        tension_model_k = partial(
            dgb.preferredAreaSurfaceTensionModel,
            modulus=self.tension_modulus,
            # preferredArea=self.geometry.getSurfaceArea(),
            preferredArea=preferred_area_k,  # self.tension_model_spec["preferred_area"],
        )

        # update the tension and osmotic params
        parameters = new_parameters(self.param_spec)
        parameters.tension.form = tension_model_k
        parameters.osmotic.form = osmotic_model_k

        # instantiate and initialize kth system using Geometry, proteinDensity, velocity, and parameters
        protein_density_k = np.array(state["protein_density"])
        velocities_k = np.array(state["velocities"])

        # we parameterize the kth system with the stateful geometry that has been updated with the latest vertex coordinates
        # system_k = dg.System(
        #     geometry=self.geometry,
        #     proteinDensity=protein_density_k,
        #     velocity=velocities_k,
        #     parameters=self.parameters,
        # )
        self.system.parameters = parameters
        # self.system.initialize(True)
        self.system.updateConfigurations()
        # system_k.initialize()

        duration_k = interval + state['duration']# self.iterations + 1

        # set up solver and parse time params
        output_dir_k = Path(tmp.mkdtemp())
        # integrator_k = dg.Euler(
        #     system=self.system,  # system_k,
        #     characteristicTimeStep=self.characteristic_time_step,  # dt
        #     savePeriod=interval,  #
        #     totalTime=interval,  # is this what we want: atomic time step or should this be related to the interval? Isn't dt always 1 anyway in this context?
        #     tolerance=self.tolerance,
        #     outputDirectory=str(output_dir_k)
        # )
        integrator_k = dg.VelocityVerlet(
            system=self.system,
            characteristicTimeStep=self.characteristic_time_step,
            totalTime=interval,
            savePeriod=interval,
            tolerance=self.tolerance,
            outputDirectory=str(output_dir_k)
        )
        # integrator_k = dg.ConjugateGradient(
        #     system=self.system,
        #     characteristicTimeStep=self.characteristic_time_step,
        #     totalTime=interval,
        #     savePeriod=interval,
        #     tolerance=self.tolerance,
        #     outputDirectory=str(output_dir_k)
        # )
        integrator_k.ifPrintToConsole = self.console_output
        integrator_k.ifOutputTrajFile = True

        # run integration
        success = integrator_k.integrate()  # or should this be integrator_k.step(interval)?

        # uncomment and implement below for IO style update
        # output_path_k = str(output_dir_k / "traj.nc")
        # data = Dataset(output_path_k, 'r')

        # get kth protein densities from kth system
        output_protein_density = self.system.getProteinDensity().tolist()

        # get kth velocities from kth system
        output_velocities = self.system.getVelocity().tolist()

        # verify geometry instance by getting it from the system (in case it has mutated). TODO: is this needed?
        output_geometry = {
            "faces": self.geometry.getFaceMatrix().tolist(),
            "vertices": self.geometry.getVertexMatrix().tolist(),
        }

        # get kth volume and surface area from output geometry
        vol_variation_vectors = self.geometry.getVertexVolumeVariationVectors()  # TODO: this is not yet used
        output_volume = self.geometry.getVolume()
        output_surface_area = self.geometry.getSurfaceArea()

        # get kth mechanical force vectors (that is, the net sum of x, y, and z vectors for each vertex)
        forces_k = self.system.getForces()
        output_force_vectors = forces_k.getMechanicalForceVec().tolist()

        # clean up temporary files
        shutil.rmtree(str(output_dir_k))
        print(f'Duration at interval {interval}: {interval}')
        self.iterations += 1

        return {
            'geometry': output_geometry,
            'protein_density': output_protein_density,
            'velocities': output_velocities,
            'volume': output_volume,
            'preferred_volume': preferred_volume_k,
            'reservoir_volume': reservoir_volume_k,
            'surface_area': output_surface_area,
            'net_forces': output_force_vectors,
            'duration': interval,
        }
