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
        self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
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

    def initial_state(self):
        # TODO: get initial parameters, return type??
        initial_parameters = parse_parameters(self.initial_parameters)
        return {
            "geometry": {
                "faces": self.initial_faces,
                "vertices": self.initial_vertices,
            },
            "parameters": initial_parameters,
            "velocities": [[] for _ in self.initial_vertices]
        }

    def inputs(self):
        return {
            "geometry": {
                "faces": "list[list[float]]",
                "vertices": "list[list[float]]",
            },
            "parameters": "tree[float]",
            "velocities": "list[list[float]]"
        }

    def outputs(self):
        return {
            "geometry": {
                "faces": "list[list[float]]",
                "vertices": "list[list[float]]",
            },
            "parameters": "tree[float]",
            "velocities": "list[list[float]]"
        }

    def update(self, state, interval):
        # take in previous geometry for k
        previous_geometry = state.get("geometry")
        previous_faces = np.array(previous_geometry["faces"], dtype=np.uint32)
        previous_vertices = np.array(previous_geometry["vertices"], dtype=np.float64)
        geometry_k = dg.Geometry(previous_faces, previous_vertices)

        # take in parameters k and set them
        parameters_k = dg.Parameters()
        param_spec = state.get("parameters")
        if param_spec:
            for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregiation, bending, etc
                attribute = getattr(parameters_k, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)

        # instantiate the params with the class pressure models
        parameters_k.tension.form = self.tension_model
        parameters_k.osmotic.form = self.osmotic_model

        # mk temp dir to parse kth outputs
        system_k = dg.System(
            geometry=geometry_k,
            parameters=parameters_k
        )
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
        success = fe.integrate()
        output_path = str(output_dir / "traj.nc")
        data = Dataset(output_path, 'r')

        # get velocities
        velocities_k = extract_data(dataset=data, data_name="velocities")

        # get faces (do we need this?)
        faces_k = extract_data(dataset=data, data_name="topology")

        # get vertices
        vertices_k = extract_data(dataset=data, data_name="coordinates")

        # parse parameters for iteration
        param_data_k = parse_parameters(parameters=parameters_k)

        # clean up temporary files
        shutil.rmtree(str(output_dir))

        return {
            "geometry": {
                "vertices": vertices_k,
                "faces": faces_k,
            },
            "parameters": param_data_k,
            "velocities": velocities_k
        }


def parse_parameters(parameters: dg.Parameters):
    # parse parameters for iteration
    param_data = {}
    for param_attr_name in dir(parameters):
        if not param_attr_name.startswith("__"):
            param_data[param_attr_name] = {}
            attr = getattr(parameters, param_attr_name)
            attr_props = {}
            for inner_name in dir(attr):
                if not inner_name.startswith("__"):
                    inner_attr = getattr(attr, inner_name)
                    if not callable(inner_attr) or not inspect.isbuiltin(inner_attr):
                        attr_props[inner_name] = inner_attr

            param_data[param_attr_name] = attr_props

    return param_data


def parse_ply(file_path: os.PathLike[str]) -> Tuple[np.ndarray, np.ndarray]:
    with open(file_path, 'r') as file:
        lines = file.readlines()
    vertex_matrix = []
    face_matrix = []
    vertex_count = 0
    face_count = 0
    in_vertex_section = False
    in_face_section = False
    for line in lines:
        line = line.strip()
        if line.startswith("element vertex"):
            vertex_count = int(line.split()[-1])
        elif line.startswith("element face"):
            face_count = int(line.split()[-1])
        elif line == "end_header":
            in_vertex_section = True
            continue

        # vertices
        if in_vertex_section:
            if len(vertex_matrix) < vertex_count:
                vertex_matrix.append(list(map(float, line.split())))
                if len(vertex_matrix) == vertex_count:
                    in_vertex_section = False
                    in_face_section = True
            continue

        # faces
        if in_face_section:
            if len(face_matrix) < face_count:
                parts = list(map(int, line.split()))
                face_matrix.append(parts[1:])  # Skip the first number (vertex count)
                if len(face_matrix) == face_count:
                    break

    return np.array(face_matrix, dtype=np.uint64), np.array(vertex_matrix, dtype=np.float64)


def extract_data(
        dataset: Dataset,
        data_name: str,
        return_last: bool = True
) -> List[Union[List[float], List[List[float]]]]:
    traj_data = dataset.groups['Trajectory'].variables[data_name][:]
    outputs = []
    for data_t in outputs:
        outputs_t = [
            [data_t[i], data_t[i + 1], data_t[i + 2]] for i in range(0, len(data_t), 3)
        ]
        outputs.append(outputs_t)
    return outputs[-1] if return_last else outputs


def generate_faces(width, height):
    """
    Generate face data for a grid mesh.
    Each face is represented as a list of vertex indices.

    Parameters:
        width (int): Number of vertices along the grid width.
        height (int): Number of vertices along the grid height.

    Returns:
        list of list: Each inner list represents a triangular face.
    """

    faces = []
    for i in range(height - 1):
        for j in range(width - 1):
            # Vertex indices of the current grid cell (as a quad)
            v0 = i * width + j
            v1 = v0 + 1
            v2 = v0 + width
            v3 = v2 + 1

            # Split the quad into two triangles
            faces.append([v0, v1, v2])  # Triangle 1
            faces.append([v1, v3, v2])  # Triangle 2
    return faces


def save_mesh_to_ply(vertices, faces, output_path):
    """
    Save vertex and face data to a PLY file.

    Parameters:
        vertices (list of tuples): List of (x, y, z) coordinates for vertices.
        faces (list of lists): List of faces, each represented by a list of vertex indices.
        output_path (str): Path to save the .ply file.
    """
    num_vertices = len(vertices)
    num_faces = len(faces)

    # PLY header
    header = f"""ply
    format ascii 1.0
    element vertex {num_vertices}
    property float x
    property float y
    property float z
    element face {num_faces}
    property list uint8 int32 vertex_indices
    end_header
    """

    # Write the PLY file
    with open(output_path, 'w') as ply_file:
        # Write header
        ply_file.write(header)

        # Write vertex data
        for x, y, z in vertices:
            ply_file.write(f"{x} {y} {z}\n")

        # Write face data
        for face in faces:
            face_str = f"{len(face)} " + " ".join(map(str, face))
            ply_file.write(f"{face_str}\n")


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


