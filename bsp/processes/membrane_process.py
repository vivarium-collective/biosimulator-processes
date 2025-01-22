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
    config_schema = {
        'mesh_file': 'string',
        'geometry': {
            'type': 'string',  # if used, ie; 'icosphere'
            'params': 'tree'  # params required for aforementioned shape type
        },
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
        'total_time': 'integer',
        'growth_coefficient': 'integer',  # growth to volume coeff ?
    }

    def __init__(self, config: Dict[str, Union[Dict[str, float], str]] = None, core: ProcessTypes = None):
        super().__init__(config, core)
        # get simulation params
        self.save_period = self.config.get("save_period", 100)  # interval at which sim state is saved to disk/recorded
        self.tolerance = self.config.get("tolerance", 1e-11)
        self.characteristic_time_step = self.config.get("characteristic_time_step", 2)
        self.total_time = self.config.get("total_time", 100)
        # that should be given to the composite?:
        self.total_time = self.config.get("total_time", 1000)
        self.default_growth_coefficient = self.config.get("growth_coefficient", 100)

        # parse input of either mesh file or geometry spec
        mesh_file = self.config.get("mesh_file")
        geometry = self.config.get("geometry")
        if mesh_file:
            self.initial_faces, self.initial_vertices = parse_ply(mesh_file)
        else:
            shape = self.config['geometry']['type']
            mesh_constructor = getattr(dg, f'get{shape.replace(shape[0], shape[0].upper())}')
            self.initial_faces, self.initial_vertices = mesh_constructor(**self.config['geometry']['params'])

        # set parameters TODO: should this be dynamic?
        self.parameters = dg.Parameters()
        init_param_spec = self.config.get("parameters")
        if init_param_spec:
            for attribute_name, attribute_spec in init_param_spec.items():  # ie: adsorption, aggregation, bending, etc
                attribute = getattr(self.parameters, attribute_name)
                for name, value in attribute_spec.items():
                    setattr(attribute, name, value)

        self.default_preferred_volume = self.config["osmotic_model"]["preferredVolume"],  # make input port here if value has changed (fba)
        self.default_reservoir_volume = self.config["osmotic_model"]["reservoirVolume"],  # output port
        self.default_osmotic_strength = self.config["osmotic_model"]["strength"]

    def initial_state(self):
        initial_geometry = {
            "faces": self.initial_faces.tolist(),
            "vertices": self.initial_vertices.tolist(),
        }
        initial_velocities = [[0.0] for _ in self.initial_vertices]
        return {
            "geometry": initial_geometry,
            "velocities": initial_velocities,
        }

    def inputs(self):
        return {
            'geometry': 'GeometryParams',  # faces: {[[]]}, vertices: [[]]}
            'species_concentrations': 'tree[float]',  # like {'species_concentrations': {'osmotic': {}, etc}}
            'fluxes': 'tree[float]',
            'growth_coefficient': 'float',
            # 'preferred_volume': 'float',  # param for osmotic pressure model
            # 'current_volume': 'float',  # param for osmotic pressure model
            # 'tension_model': 'TensionModelParams',  # todo: can we parse this from the previous two fields?
            # 'species_concentrations': 'tree[float]',  # particularly, preferred volume
            # 'fluxes': 'tree[float]',  # parsing preferred volume from dfba outputs?
        }

    def outputs(self):
        return {
            'geometry': 'GeometryParams',
            'velocities': 'list'
        }

    def update(self, state, interval):
        # parse kth-1 geometry output
        previous_geometry = state.get("geometry")
        input_faces = previous_geometry["faces"]
        input_vertices = previous_geometry["vertices"]
        previous_faces = np.array(input_faces) if isinstance(input_faces, list) else input_faces
        previous_vertices = np.array(input_vertices) if isinstance(input_vertices, list) else input_vertices

        # instantiate new geometry for k
        geometry_k = dg.Geometry(previous_faces, previous_vertices)

        # calculate current volume from kth inputs
        input_fluxes = state.get("fluxes")
        input_osmotic_species_concentrations = state.get("species_concentrations").get('osmotic')
        total_osmotic_concentration = sum(input_osmotic_species_concentrations.values())
        n_solutes = sum(input_fluxes[reaction] for reaction in input_fluxes if "transport" in reaction)
        volume_k = n_solutes / total_osmotic_concentration

        # calculate preferred volume
        # nutrient_concentration = 0.5
        # Km = 0.3  # Michaelis constant
        # k_base = 1000  # Baseline coefficient
        # growth_to_volume_coeff = k_base * (1 + nutrient_concentration / (Km + nutrient_concentration))
        input_growth_coeff = state.get("growth_coefficient", self.default_growth_coefficient)
        growth_flux = input_fluxes.get("biomass_reaction", 0)
        growth_volume = input_growth_coeff * growth_flux
        osmotic_volume = volume_k  # TODO: this assumes the osmotic contribution directly determines the volume of the cell at equilibrium
        preferred_volume_k = volume_k + osmotic_volume * 1e12 + growth_volume  # converts to L TODO: how should we handle units?
        osmotic_strength_k = state.get("osmotic_strength", self.default_osmotic_strength)

        # set osmotic model callback
        osmotic_model_k = partial(
            dgb.preferredVolumeOsmoticPressureModel,
            preferredVolume=preferred_volume_k,  # make input port here if value has changed (fba)
            volume=volume_k,  # output port
            strength=osmotic_strength_k,
        )

        # calculate area and preferred area from volume params
        radius_k = (3 * volume_k / (4 * np.pi)) ** (1/3)
        area_k = 4 * np.pi * radius_k**2
        preferred_radius_k = (3 * preferred_volume_k / (4 * np.pi)) ** (1 / 3)
        preferred_area_k = 4 * np.pi * preferred_radius_k ** 2

        # set tension model callback
        tension_model_k = partial(
            dgb.preferredAreaSurfaceTensionModel,
            area=area_k,
            modulus=self.config["tension_model"]["modulus"],
            preferredArea=preferred_area_k,
        )

        # instantiate the params with the class pressure models
        param_config = state.get("parameters", self.config["parameters"])
        parameters_k = new_parameters(param_spec=param_config)
        parameters_k.tension.form = tension_model_k
        parameters_k.osmotic.form = osmotic_model_k

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


def new_parameters(param_spec: Dict) -> dg.Parameters:
    parameters = dg.Parameters()
    if param_spec:
        for attribute_name, attribute_spec in param_spec.items():  # ie: adsorption, aggregation, bending, etc
            attribute = getattr(parameters, attribute_name)
            for name, value in attribute_spec.items():
                setattr(attribute, name, value)

    return parameters


def test_membrane_process():
    # get vertices this will be divisible by 3 and thus is a time indexed flat list of tuples(xyz) for each vertex in the mesh
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


