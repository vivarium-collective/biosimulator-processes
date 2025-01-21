import inspect
import os
from typing import Tuple, Union, List

import numpy as np
import pymem3dg as dg
from h5py import Dataset


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
        return_last: bool = True,
        use_numpy: bool = False
) -> List[Union[List[float], List[List[float]]]]:
    traj_data = dataset.groups['Trajectory'].variables[data_name][:]
    traj_data = traj_data.tolist() if use_numpy else traj_data
    outputs = []
    for data_t in traj_data:
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