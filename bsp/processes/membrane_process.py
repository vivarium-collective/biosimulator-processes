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


class MembraneProcess(Process):
    """
    Membrane process consisting of preferredAreaSurfaceTension and preferredVolumeOsmoticPressure models (expand and contract)

    :config mesh_file: input .ply file TODO: generalize this
    :config tension_model:
    :config osmotic_model:
    :config parameters: dict[str, float]: {**dir(pymem3dg.Parameters()}: 'adsorption', 'aggregation', 'bending', 'boundary', 'damping', 'dirichlet', 'dpd',
        entropy', 'external', 'osmotic', 'point', 'protein', 'proteinMobility', 'selfAvoidance', 'spring', 'temperature', 'tension', 'variation'.

    """
    config_schema = {
        'mesh_file': 'string',
        'tension_model': 'tree[float]',
        'osmotic_model': 'tree[float]',
        # 'tension_model': {
        #     'modulus': 'float',
        #     'preferredArea': 'float'
        # },
        # 'osmotic_model': {
        #     'preferredVolume': 'float',
        #     'reservoirVolume': 'float',
        #     'strength': 'float'  # what units is this in??
        # },
        'parameters': 'tree[any]',
        'save_period': 'integer',
        'tolerance': 'float',
        'characteristic_time_step': 'integer',
        'total_time': 'integer'
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)

        # get simulation params
        self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
        self.total_time = self.config.get("total_time", 100)
        # that should be given to the composite?:
        # self.total_time = self.config.get("total_time", 10000)

        # create geometry from model file
        self.initial_faces, self.initial_vertices = parse_ply(self.config["mesh_file"])

        # set the surface area tension model
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

        self.initial_parameters.tension.form = self.tension_model
        self.initial_parameters.osmotic.form = self.osmotic_model

        # TODO: would this be helpful to represent an evolving system?
        self.system = partial(
            dg.System,
            parameters=self.initial_parameters,
        )

        self.velocities_type = 'list'  # np.array

        # TODO: is this okay for both ports?
        self.port_schema = {
            "geometry": {
                "faces": "list[list[integer]]",
                "vertices": "list[list[float]]",
            },
            'velocities': 'list[list[float]]',
            # "geometry": 'map[map[list[float]]]',
            # "parameters": "tree[float]",
            # "velocities": "list[list[float]]"
        }

        self.faces_type = np.array(self.initial_faces)
        self.vertices_type = np.array(self.initial_vertices)

    def initial_state(self):
        # TODO: get initial parameters, return type??
        # initial_parameters = parse_parameters(self.initial_parameters)
        initial_geometry = {
                "faces": self.initial_faces.tolist(),
                "vertices": self.initial_vertices.tolist(),
        }
        initial_velocities = [[0.0] for _ in self.initial_vertices]
        return {
            "geometry": initial_geometry,
            # "parameters": initial_parameters,
            "velocities": np.array(initial_velocities) if self.velocities_type == 'array' else initial_velocities
        }

    def inputs(self):
        return self.port_schema

    def outputs(self):
        return self.port_schema

    def update(self, state, interval):
        # take in previous geometry for k
        previous_geometry = state.get("geometry")
        input_faces = previous_geometry["faces"]
        input_vertices = previous_geometry["vertices"]
        previous_faces = np.array(input_faces, dtype=np.uint32) if isinstance(input_faces, list) else input_faces
        previous_vertices = np.array(input_vertices, dtype=np.float64) if isinstance(input_vertices, list) else input_vertices
        geometry_k = dg.Geometry(previous_faces, previous_vertices)

        # take in parameters k and set them
        # parameters_k = dg.Parameters()
        # param_spec = state.get("parameters")
        # if param_spec:
        #     for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregiation, bending, etc
        #         attribute = getattr(parameters_k, attribute_name)
        #         for name, value in attribute_spec.items():
        #             setattr(attribute, name, value)

        # instantiate the params with the class pressure models
        # parameters_k.tension.form = self.tension_model
        # parameters_k.osmotic.form = self.osmotic_model

        # mk temp dir to parse kth outputs
        # system_k = dg.System(
        #     geometry=geometry_k,
        #     parameters=self.initial_parameters,
        #     # parameters = parameters_k
        # )
        system_k = self.system(geometry=geometry_k)
        system_k.initialize()

        # set up solver
        output_dir = Path(tmp.mkdtemp())
        fe = dg.Euler(
            system=system_k,
            characteristicTimeStep=self.characteristic_time_step,
            savePeriod=self.save_period,
            totalTime=1,  # interval?
            tolerance=self.tolerance,
            outputDirectory=str(output_dir)
        )
        fe.ifPrintToConsole = True
        fe.ifOutputTrajFile = True

        # run solver and extract data
        success = fe.integrate()  # or should this be fe.step(interval)?
        output_path = str(output_dir / "traj.nc")
        data = Dataset(output_path, 'r')

        # get velocities
        velocities_k = extract_data(dataset=data, data_name="velocities", return_last=False)

        # get faces (do we need this?)
        faces_k = extract_data(dataset=data, data_name="topology", return_last=False)

        # get vertices
        vertices_k = extract_data(dataset=data, data_name="coordinates", return_last=False)

        # parse parameters for iteration
        # param_data_k = parse_parameters(parameters=parameters_k)

        # clean up temporary files
        shutil.rmtree(str(output_dir))

        geometry_out = {
            "vertices": vertices_k,
            "faces": faces_k,
        }

        return {
            "geometry": geometry_out,
            # "parameters": param_data_k,
            "velocities": velocities_k
        }


# get vertices this will be divisible by 3 and thus is a time indexed flat list of tuples(xyz) for each vertex in the mesh
# vertex_data = data.groups['Trajectory'].variables['coordinates'][:]
# vertices = []
# for v_t in vertex_data:
#     vertices_t = [
#         [v_t[i], v_t[i + 1], v_t[i + 2]] for i in range(0, len(v_t), 3)
#     ]
#     vertices.append(vertices_t)
# vertices_k = vertices[-1]
# vertices_k = [vertex_data[-1][::3], vertex_data[-1][1::3], vertex_data[-1][2::3]]


def test_membrane_process():
    from bsp import app_registrar

    # define config and port vals
    test_config = {
        'mesh_file': '/Users/alexanderpatrie/Desktop/repos/biosimulator-processes/tests/fixtures/sample_meshes/oblate.ply',
        'tension_model': {
            'modulus': 0.1,
            'preferredArea': 12.4866
        },
        'osmotic_model': {
            'preferredVolume': 0.7 * np.pi * 4 / 3,
            'reservoirVolume': 0,
            'strength': 0.02
        },
        'parameters': {
            'bending': {
                'Kbc': 8.22e-5
            }
        },
        'save_period': 100,
        'tolerance': 1e-11,
        'characteristic_time_step': 2
    }

    port_schema = {
        "geometry": {
            "faces": ["faces_store"],
            "vertices": ["vertices_store"],
        },
        "parameters": ["parameters_store"],
        "velocities": ["velocities_store"]
    }

    # register process
    app_registrar.register_process("membrane-process", MembraneProcess, verbose=True)

    # create spec
    document = new_document(
        name='membrane',
        address='membrane-process',
        _type='process',
        config=test_config,
        inputs=port_schema,
        outputs=port_schema,
        add_emitter=True
    )

    # configure and run composite
    sim = Composite(
        config={'state': document},
        core=app_registrar.core
    )
    total_time = 10000
    sim.run(total_time)

    # get results
    data = sim.gather_results()
    pp(data)


