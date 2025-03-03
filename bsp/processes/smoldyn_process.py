"""The output data returned by that which is required by simularium (executiontime, listmols),
    when written and read into the same file for a given global time is as follows:

    [identity, state, x, y, z, serial number], where:

        identity = species identity for molecule
        state = state of the given molecule
        x, y, z = values for the relative coordinates
        serial_number = monotonically decreasing timestamp for the given species_id

        At each global timestep (`executiontime`), a new 'cast of characters' are introduced that may resemble the
            cast of characters at the first timestep, but are in fact different and thus all the molecules provided
            from the `listmols` command will in fact all be unique.


    I propose the following consideration at each `update` step:

    The `smoldyn.Simulation().connect()` method can be used to (for example) tell the
    simulation about external environmental parameters that change over the course of
    the simulation. For example:

        a = None
        avals = []

        def new_difc(t, args):
            global a, avals
            x, y = args
            avals.append((t, a.difc['soln']))
            return x * math.sin(t) + y

        def update_difc(val):
            global a
            a.difc = val

        def test_connect():
            global a, avals
            sim = smoldyn.Simulation(low=(.......
            a = sim.addSpecies('a', color=black, difc=0.1)

            # specify either function as target:
            sim.connect(new_dif, update_difc, step=10, args=[1,1])

            # ...or species as target:
            sim.connect(func = new_dif, target = 'a.difc', step=10, args=[0, 1])

            sim.run(....


"""
import math
import os
from dataclasses import dataclass
from typing import *
from uuid import uuid4

import numpy as np
from process_bigraph import Process, Composite, pf, pp

from bsp.data_model.base import BaseClass
from bsp.data_model.sed import SedModel

try:
    import smoldyn as sm
    from smoldyn._smoldyn import MolecState, Simulation
except:
    raise ImportError(
        '\nPLEASE NOTE: Smoldyn is not correctly installed on your system which prevents you from ' 
        'using the SmoldynProcess. Please refer to the README for further information '
        'on installing Smoldyn.'
    )


class SmoldynProcess(Process):
    config_schema = {
        'model': 'SedModelConfig',
        'animate': {
            '_type': 'boolean',
            '_default': False
        }
    }

    def __init__(self, config: Dict[str, Any] = None, core=None):
        """A new instance of `SmoldynProcess` based on the `config` that is passed. The schema for the config to be passed in
            this object's constructor is as follows:

            config_schema = {
                'model_filepath': 'string',  <-- analogous to python `str`
                'animate': 'bool'  <-- of type `bigraph_schema.base_types.bool`

            # TODO: It would be nice to have classes associated with this.
        """
        super().__init__(config, core)

        # specify the model fp for clarity
        # self.model_filepath = self.config.get('model_filepath')
        self.model_filepath = self.config.get('model').get('model_source')

        # enforce model filepath passing
        if not self.model_filepath:
            raise ValueError(
                '''
                    The Process configuration requires a Smoldyn model filepath to be passed.
                    Please specify a 'model_filepath' in your instance configuration.
                '''
            )

        # initialize the simulator from a Smoldyn MinE.txt file.
        self.simulation: sm.Simulation = sm.Simulation.fromFile(self.model_filepath)

        # get a list of the simulation species
        species_count = self.simulation.count()['species']
        self.species_names: List[str] = []
        for index in range(species_count):
            species_name = self.simulation.getSpeciesName(index)
            if 'empty' not in species_name.lower():
                self.species_names.append(species_name)
        # sort for logistical mapping to species names (i.e: ['a', 'b', c'] == ['0', '1', '2']
        self.species_names.sort()

        # make species counts of molecules dataset for output
        self.simulation.addOutputData('species_counts')
        # write molcounts to counts dataset at every timestep (shape=(n_timesteps, 1+n_species <-- one for time)): [timestep, countSpec1, countSpec2, ...]
        self.simulation.addCommand(cmd='molcount species_counts', cmd_type='E')

        # make molecules dataset (molecule information) for output
        self.simulation.addOutputData('molecules')
        # write coords to dataset at every timestep (shape=(n_output_molecules, 7)): seven being [timestep, smol_id(species), mol_state, x, y, z, mol_serial_num]
        self.simulation.addCommand(cmd='listmols2 molecules', cmd_type='E')

        # initialize the molecule ids based on the species names. We need this value to properly emit the schema, which expects a single value from this to be a str(int)
        # the format for molecule_ids is expected to be: 'speciesId_moleculeNumber'
        self.molecule_ids: List[str] = [str(uuid4()) for n in list(range(len(self.species_names)))]

        # get the simulation boundaries, which in the case of Smoldyn denote the physical boundaries
        # TODO: add a verification method to ensure that the boundaries do not change on the next step...
        self.boundaries: Dict[str, List[float]] = dict(zip(['low', 'high'], self.simulation.getBoundaries()))

        # set graphics (defaults to False)
        if self.config['animate']:
            self.simulation.addGraphics('opengl_better')

        # create a re-usable counts and molecules type to be used by both inputs and outputs
        self.counts_type = {
            species_name: 'integer'
            for species_name in self.species_names
        }

        self.port_schema = {
            'species_counts': {
                species_name: 'integer'
                for species_name in self.species_names
            },
            'molecules': 'tree[float]',  # self.molecules_type
            'geometry': 'GeometryType',
            'forces': 'list',
        }

        self._specs = [None for _ in self.species_names]
        self._vals = dict(zip(self.species_names, [[] for _ in self.species_names]))

    def initial_state(self) -> Dict[str, Union[int, Dict]]:
        """Set the initial parameter state of the simulation. This method should return an implementation of
            that which is returned by `self.schema()`.


        NOTE: Due to the nature of this model,
            Smoldyn assigns a random uniform distribution of integers as the initial coordinate (x, y, z)
            values for the simulation. As such, the `set_uniform` method will uniformly distribute
            the molecules according to a `highpos`[x,y] and `lowpos`[x,y] where high and low pos are
            the higher and lower bounds of the molecule spatial distribution.

            NOTE: This method should provide an implementation of the structure denoted in `self.schema`.
        """
        # get the initial species counts
        initial_species_counts = {
            spec_name: self.simulation.getMoleculeCount(spec_name, MolecState.all)
            for spec_name in self.species_names
        }

        return {
            'geometry': {
                'faces': [],
                'vertices': []
            },
            'forces': [],
            'species_counts': initial_species_counts,
            'molecules': {
                mol_id: {
                    'coordinates': [0.0, 0.0, 0.0],
                    'species_id': self.species_names[i],
                    'state': 0
                }
                for i, mol_id in enumerate(self.molecule_ids)
            }
        }

    def inputs(self):
        species_counts_schema = {
            species_name: 'integer'
            for species_name in self.species_names
        }
        return {
            'species_counts': species_counts_schema,
            'particles': 'ParticleType',
            'geometry': 'GeometryType',
            'net_forces': 'MechanicalForcesType',
            'notable_vertices': 'list[boolean]'
        }

    def outputs(self):
        species_counts_schema = {
            species_name: 'integer'
            for species_name in self.species_names
        }
        return {
            'species_counts': species_counts_schema,
            'particles': 'ParticleType',
            # 'geometry': 'GeometryType',
            # 'net_forces': 'MechanicalForcesType'
        }

    def update(self, state: Dict, interval: int) -> Dict:
        """TODO: We must account for the mol_ids that are generated in the output based on the interval run,
                i.e: Shorter intervals will yield both less output molecules and less unique molecule ids.
        """
        # take in geometry from state
        vertices_k = np.array(state['geometry']['vertices'])

        # get upper and lower boundary coords from vertices: iterate over each axis and get max of each axis
        bounds_low, bounds_high = get_kth_boundaries(vertices_k)

        # reset the molecules, distribute the mols according to dynamic bounds
        for name in self.species_names:
            set_uniform(
                simulation=self.simulation,
                species_name=name,
                boundary_high=max(bounds_high),
                boundary_low=min(bounds_low),
                count=state['species_counts'][name],
                kill_mol=False
            )

            # TODO: extract the difc from the model somehow!
            # d0 = self.simulation.getSpecies(name).difc
            d0 = 0.3  # placeholder difc
            forces_k = np.array(state['net_forces'])
            alpha = 0.3  # TODO: make this not arbitrary
            beta = 1.0

            # TODO: we need to take in noticeable vertices from the membrane force prescription and infer beta for given particle based on its coords at iteration k
            # derive beta based on the given particle's distance at iteration k from the membrane (bounds)

            self.simulation.connect(
                func=compute_kth_difc,
                target=f'{name}.difc',
                step=interval,
                args=[d0, forces_k, alpha, beta],
            )

        # run the simulation for a given interval
        self.simulation.run(
            stop=interval,
            dt=self.simulation.dt
        )

        # get the counts data, clear the buffer
        counts_data = self.simulation.getOutputData('species_counts')

        # get the final counts for the update
        final_count = counts_data[-1]

        # remove the timestep from the list
        final_count.pop(0)

        # get the data based on the commands added in the constructor, clear the buffer
        molecules_data = self.simulation.getOutputData('molecules')

        # create an empty simulation state mirroring that which is specified in the schema
        simulation_state = {
            'species_counts': {},
            'particles': {}
        }

        # get and populate the species counts
        for index, name in enumerate(self.species_names):
            input_counts = state['species_counts'][name]
            simulation_state['species_counts'][name] = int(final_count[index]) - input_counts

        # clear the list of known molecule ids and update the list of known molecule ids (convert to an intstring)
        self.molecule_ids.clear()
        for molecule in molecules_data:
            self.molecule_ids.append(str(uuid4()))

        # get and populate the output molecules
        for index, mol_id in enumerate(self.molecule_ids):
            single_molecule_data = molecules_data[index]
            single_molecule_species_index = int(single_molecule_data[1]) - 1

            simulation_state['particles'][mol_id] = {
                'coordinates': single_molecule_data[3:6],
                'species_id': self.species_names[single_molecule_species_index],
                'state': str(int(single_molecule_data[2]))
            }

        # TODO -- post processing to get effective rates

        return simulation_state


# TODO: finish this
@dataclass
class Boundary(BaseClass):
    low: tuple[list[float], list[float]]
    high: tuple[list[float], list[float]]


def get_axis_vertices(vertices, axis: int, func):
    return func([vertex[axis] for vertex in vertices])


def get_bounds(vertices, axis: int) -> tuple[float, float]:
    ax_min = get_axis_vertices(vertices, axis, min)
    ax_max = get_axis_vertices(vertices, axis, max)
    return ax_min, ax_max


def get_kth_boundaries(vertices) -> tuple[list[float], list[float]]:
    """

    """
    x_min, x_max = get_bounds(vertices, 0)
    y_min, y_max = get_bounds(vertices, 1)
    z_min, z_max = get_bounds(vertices, 2)

    return [x_min, y_min, z_min], [x_max, y_max, z_max]


def compute_kth_difc(t, args):
    """
    Called by `smoldyn.Simulation` during the kth iteration (t) of `SmoldynProcess.update()`.

    :param t: time step of kth iteration.
    :param args: arguments required to compute an updated difc for each particle at iteration k in `SmoldynProcess.update()`. The
        arguments are:
        D0: difc for species s at iteration k.
        forces: the force vector matrix from the membrane at iteration k.
        alpha: membrane vertex force sensitivity constant based on membrane construction and make-up.
        beta: a force sensitivity constant based on particle location from membrane.
    """
    # TODO: make alpha and beta more formal/expandable terms
    # alpha = 0.5, beta = 1.0

    D0, forces, distance, alpha, beta = args
    if not isinstance(forces, np.ndarray):
        forces = np.array(forces)

    force_magnitude = np.linalg.norm(forces)
    alpha_scaled = alpha * np.exp(-beta * distance)

    return D0 * np.exp(-alpha_scaled * force_magnitude)


def set_uniform(
        simulation: Simulation,
        species_name: str,
        count: int,
        boundary_high: float,
        boundary_low: float,
        kill_mol: bool = True
) -> None:
    """Add a distribution of molecules to the solution in
        the simulation memory given a higher and lower bound x,y coordinate. Smoldyn assumes
        a global boundary versus individual species boundaries. Kills the molecule before dist if true.
        TODO: If pymunk expands the species compartment, account for
              expanding `highpos` and `lowpos`. This method should be used within the body/logic of
              the `update` class method.
    """
    # kill the mol, effectively resetting it
    if kill_mol:
        simulation.runCommand(f'killmol {species_name}')

    # TODO: eventually allow for an expanding boundary ie in the configuration parameters (pymunk?), which is defies the methodology of smoldyn

    # redistribute the molecule according to the bounds
    return simulation.addSolutionMolecules(
        species=species_name,
        number=count,
        highpos=boundary_high,
        lowpos=boundary_low
    )




# -- SMOLDYN IO PROCESS FOR SIMULARIUM -- #

class SmoldynIOProcess(Process):
    """
    Parameters:
        model: model: {model_source: INPUT FILEPATH, ...}
        duration: simulation duration (int)
        output_dest: tmp output dir (str)
    """
    config_schema = {
        'model': SedModel,
        # 'duration': 'integer',  # duration should instead be inferred from Composite
        'output_dest': 'string',
        'animate': {
            '_type': 'boolean',
            '_default': False
        }
    }

    def __init__(self, config: dict = None, core=None):
        super().__init__(config, core)

        # get params
        input_filepath = self.config.get('model').get('model_source')
        input_filename = input_filepath.split('/')[-1]
        output_dest = self.config['output_dest']
        self.model_filepath = os.path.join(output_dest, input_filename)
        # self.duration = self.config['duration']

        # write the uploaded file to save dest(temp)
        with open(input_filepath, 'r') as source_file:
            with open(self.model_filepath, 'w') as model_file:
                # Read from the source file and write to the destination
                model_file.write(source_file.read())

        # get the appropriate output filepath
        self.output_filepath = self.handle_output_commands()

        # enforce model filepath passing
        if not self.model_filepath:
            raise ValueError(
                '''
                    The Process configuration requires a Smoldyn model filepath to be passed.
                    Please specify a 'model_filepath' in your instance configuration.
                '''
            )

        # initialize the simulator from a Smoldyn MinE.txt file.
        self.simulation: sm.Simulation = sm.Simulation.fromFile(self.model_filepath)

        # get a list of the simulation species
        species_count = self.simulation.count()['species']
        self.species_names: List[str] = []
        for index in range(species_count):
            species_name = self.simulation.getSpeciesName(index)
            if 'empty' not in species_name.lower():
                self.species_names.append(species_name)
        # sort for logistical mapping to species names (i.e: ['a', 'b', c'] == ['0', '1', '2']
        self.species_names.sort()
        self.port_schema = {'output_filepath': 'string'}
        self.boundaries: Dict[str, List[float]] = dict(zip(['low', 'high'], self.simulation.getBoundaries()))
        self.interval = 0

    def set_uniform(
            self,
            species_name: str,
            count: int,
            kill_mol: bool = True
    ) -> None:
        """Add a distribution of molecules to the solution in
            the simulation memory given a higher and lower bound x,y coordinate. Smoldyn assumes
            a global boundary versus individual species boundaries. Kills the molecule before dist if true.

            TODO: If pymunk expands the species compartment, account for
                  expanding `highpos` and `lowpos`. This method should be used within the body/logic of
                  the `update` class method.

            Args:
                species_name:`str`: name of the given molecule.
                count:`int`: number of molecules of the given `species_name` to add.
                kill_mol:`bool`: kills the molecule based on the `name` argument, which effectively
                    removes the molecule from simulation memory.
        """
        # kill the mol, effectively resetting it
        if kill_mol:
            self.simulation.runCommand(f'killmol {species_name}')

        # TODO: eventually allow for an expanding boundary ie in the configuration parameters (pymunk?), which is defies the methodology of smoldyn

        # redistribute the molecule according to the bounds
        self.simulation.addSolutionMolecules(
            species=species_name,
            number=count,
            highpos=self.boundaries['high'],
            lowpos=self.boundaries['low']
        )

    def initial_state(self) -> Dict[str, Union[int, Dict]]:
        """Set the initial parameter state of the simulation. This method should return an implementation of
            that which is returned by `self.schema()`.


        NOTE: Due to the nature of this model,
            Smoldyn assigns a random uniform distribution of integers as the initial coordinate (x, y, z)
            values for the simulation. As such, the `set_uniform` method will uniformly distribute
            the molecules according to a `highpos`[x,y] and `lowpos`[x,y] where high and low pos are
            the higher and lower bounds of the molecule spatial distribution.

            NOTE: This method should provide an implementation of the structure denoted in `self.schema`.
        """
        return {}

    def inputs(self):
        return {}

    def outputs(self):
        return self.port_schema

    def update(self, inputs: Dict, interval: int) -> Dict:
        """Callback method to be evoked at each Process interval. We want to get the
            last of each dataset type as that is the relevant data in regard to the Process timescale scope.

            Args:
                inputs:`Dict`: current state of the Smoldyn simulation, expressed as a `Dict` whose
                    schema matches that which is returned by the `self.schema()` API method.
                interval:`int`: Analogous to Smoldyn's `time_stop`, this is the
                    timestep interval at which to provide the update as the output of this method.
                    NOTE: This update is iteratively called with the `Process` API.

            Returns:
                `Dict`: New state according to the update at interval


            TODO: We must account for the mol_ids that are generated in the output based on the interval run,
                i.e: Shorter intervals will yield both less output molecules and less unique molecule ids.
        """
        # get current counts state from simulator instance
        species_counts = {
            spec_name: self.simulation.getMoleculeCount(spec_name, MolecState.all)
            for spec_name in self.species_names
        }

        # reset the molecules, distribute the mols according to self.boundarieså
        for name in self.species_names:
            # TODO: find a better MolecState to use
            current_species_count = self.simulation.getMoleculeCount(name, MolecState.all)
            self.set_uniform(
                species_name=name,
                count=current_species_count,
                kill_mol=True
            )

        # run the simulation for a given interval
        # self.simulation.run(
        #     stop=interval + 1,
        #     dt=self.simulation.dt
        # )
        self.simulation.runSim()

        # rewrite the modelout to a unique name
        outfile = self.output_filepath.split('/')[-1]
        output_filename = str(self.interval) + "_" + outfile
        output_filepath = self.output_filepath.replace(outfile, output_filename)
        self.interval += 1

        # return the modelout file
        return {'output_filepath': output_filepath}

    def read_smoldyn_simulation_configuration(self, filename) -> list[str]:
        ''' Read a configuration for a Smoldyn simulation

        Args:
            filename (:obj:`str`): path to model file

        Returns:
            :obj:`list` of :obj:`str`: simulation configuration
        '''
        with open(filename, 'r') as file:
            return [line.strip('\n') for line in file]

    def write_smoldyn_simulation_configuration(self, configuration, filename) -> None:
        ''' Write a configuration for Smoldyn simulation to a file

        Args:
            configuration
            filename (:obj:`str`): path to save configuration
        '''
        with open(filename, 'w') as file:
            for line in configuration:
                file.write(line)
                file.write('\n')

    def handle_output_commands(self) -> str:
        model_fp = self.model_filepath
        duration = 1
        config = self.read_smoldyn_simulation_configuration(model_fp)
        has_output_commands = any([v.startswith('output') for v in config])
        if not has_output_commands:
            cmd_i = 0
            for i, v in enumerate(config):
                if v == 'end_file':
                    cmd_i += i - 1
                stop_key = 'time_stop'

                if f'define {stop_key.upper()}' in v:
                    new_v = f'define TIME_STOP   {duration}'
                    config.remove(config[i])
                    config.insert(i, new_v)
                elif v.startswith(stop_key):
                    new_v = f'time_stop TIME_STOP'
                    config.remove(config[i])
                    config.insert(i, new_v)
            cmds = ["output_files modelout.txt",
                    "cmd i 0 TIME_STOP 1 executiontime modelout.txt",
                    "cmd i 0 TIME_STOP 1 listmols modelout.txt"]
            current = cmd_i
            for cmd in cmds:
                config.insert(current, cmd)
                current += 1

        self.write_smoldyn_simulation_configuration(config, model_fp)

        out_filepath = model_fp.replace(model_fp.split('/')[-1].split('.')[0], 'modelout')
        return out_filepath

    def _new_difc(self, t, args):
        minD_count, minE_count = args
        # TODO: extract real volume
        volume = 1.0

        # Calculate concentrations from counts
        minD_conc = minD_count / volume
        minE_conc = minE_count / volume

        # for example: diffusion coefficient might decrease with high MinD-MinE complex formation
        minDE_complex = minD_conc * minE_conc  # Simplified interaction term
        base_diffusion = 2.5  # Baseline diffusion coefficient

        # perturb the parameter of complex formation effect slightly
        _alpha = 0.1
        delta = _alpha - (_alpha ** 10)
        alpha = _alpha - delta

        new_difc = base_diffusion * (1 - alpha * minDE_complex)

        # Ensure the diffusion coefficient remains within a reasonable range
        new_difc = max(min(new_difc, base_diffusion), 0.01)  # Adjust bounds as needed

        return new_difc


def test_process(core):
    """Test the smoldyn process using the crowding model."""

    # this is the instance for the composite process to run
    print("RUNNING")
    core.process_registry.register('biosimulators_processes.processes.smoldyn_process.SmoldynProcess', SmoldynProcess)
    instance = {
        'smoldyn': {
            '_type': 'process',
            'address': 'local:!biosimulators_processes.processes.smoldyn_process.SmoldynProcess',
            'config': {
                'model_filepath': 'biosimulators_processes/model_files/minE_model.txt',
                'animate': False},
            'inputs': {
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store']},
            'outputs': {
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store']}
        },
        'emitter': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    'species_counts': 'tree[string]',
                    'molecules': 'tree[string]'}
            },
            'inputs': {
                'species_counts': ['species_counts_store'],
                'molecules': ['molecules_store']}
        }
    }

    total_time = 2

    # make the composite
    # workflow = Composite({
    #     'state': instance
    # })

    # run
    # workflow.run(total_time)

    # gather results
    # results = workflow.gather_results()
    # pp(f'RESULTS: {pf(results)}')
