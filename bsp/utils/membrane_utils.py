import inspect
import os
from pathlib import Path
from typing import Tuple, Union, List, Dict

import numpy as np
import pymem3dg as dg
from h5py import Dataset
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from process_bigraph import Composite


def reflect_forces(particles, vertex_matrix, force_vectors, time_step):
    for particle in particles:
        # Find nearest vertex
        distances = np.linalg.norm(vertex_matrix - particle.position, axis=1)
        nearest_vertex_idx = np.argmin(distances)

        # Reflect force onto the particle
        force = -force_vectors[nearest_vertex_idx]  # Reaction force
        particle.velocity += force * time_step / particle.mass


def calculate_preferred_area(v_preferred: float, convert_to_micro: bool = False) -> float:
    V_preferred = v_preferred
    V_preferred = V_preferred * 1e15 if convert_to_micro else V_preferred  # Convert liters to μm³
    r_preferred = (3 * V_preferred / (4 * np.pi)) ** (1/3)
    A_preferred = 4 * np.pi * r_preferred**2

    return A_preferred


def new_parameters(param_spec: Dict):
    parameters = dg.Parameters()
    for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregation, bending, etc
        attribute = getattr(parameters, attribute_name)
        if isinstance(attribute_spec, dict):
            for name, value in attribute_spec.items():
                setattr(attribute, name, value)
        else:
            setattr(parameters, attribute_name, attribute_spec)
    return parameters


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


def extract_last_data(
        dataset: Dataset,
        data_name: str
) -> List[Union[List[float], List[List[float]]]]:
    traj_data = dataset.groups['Trajectory'].variables[data_name][:]
    traj_data = traj_data.tolist()

    return traj_data[-1]


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


def get_vertex_coordinates(outputDir: Path) -> np.ndarray:
    data = Dataset(str(outputDir / "traj.nc"), 'r')

    # get data parameters
    variables = data.groups['Trajectory'].variables

    # get the coordinates from groups/trajectory.variables
    return data.groups['Trajectory'].variables['coordinates'][:]


def get_axis_vertices(x: np.ndarray, t) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    vertices_x = x[t][::3]
    vertices_y = x[t][1::3]
    vertices_z = x[t][2::3]
    return vertices_x, vertices_y, vertices_z


def format_vertices(x: np.ndarray, t: int, geo: dg.Geometry):
    return np.reshape(x[t], geo.getVertexMatrix().shape)


def get_animation(x: np.ndarray) -> animation.FuncAnimation:
    # Create figure and 3D axis
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    n_steps = x.shape[0]
    # Initialize scatter plot with empty data
    scat = ax.scatter([], [], [])

    vertices_x, vertices_y, vertices_z = get_axis_vertices(x, 0)

    # Set axis limits (you may need to adjust based on your data)
    ax.set_xlim(np.min(vertices_x), np.max(vertices_x))
    ax.set_ylim(np.min(vertices_y), np.max(vertices_y))
    ax.set_zlim(np.min(vertices_z), np.max(vertices_z))
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")

    # Update function for animation
    def update(frame):
        ax.set_title(f"Time step: {frame}")

        # Extract x, y, z coordinates for the current frame
        xs = x[frame][::3]
        ys = x[frame][1::3]
        zs = x[frame][2::3]

        # Update scatter plot
        scat._offsets3d = (xs, ys, zs)  # Special way to update 3D scatter plots

        return scat,

    # Create animation
    return animation.FuncAnimation(fig, update, frames=n_steps, interval=50)


def get_times(sim: Composite):
    results = sim.gather_results()[('emitter',)]
    return np.array([t for t in range(len(results))])


def get_vertices(sim: Composite, time_index: int) -> np.ndarray:
    results = sim.gather_results()[('emitter',)]
    n_vertices = len(results[0]['geometry']['vertices'])
    return np.array(results[time_index]['geometry']['vertices'][:n_vertices])


