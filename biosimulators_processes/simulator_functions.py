"""
Simulator functions derived from the update methods of Utc processes and more.
"""


from tempfile import mkdtemp
from typing import *
from importlib import import_module

import libsbml
import numpy as np

try:
    from amici import SbmlImporter, import_model_module, Model, runAmiciSimulation
except ImportError as e:
    print(e)
try:
    from basico import *
except ImportError as e:
    print(e)
try:
    import tellurium as te
except ImportError as e:
    print(e)


def get_sbml_species_mapping(sbml_fp: str):
    """

    Args:
        - sbml_fp: `str`: path to the SBML model file.

    Returns:
        Dictionary mapping of {sbml_species_names(usually the actual observable name): sbml_species_ids(ids used in the solver)}
    """
    # read file
    sbml_reader = libsbml.SBMLReader()
    sbml_doc = sbml_reader.readSBML(sbml_fp)
    sbml_model_object = sbml_doc.getModel()
    # parse and handle names/ids
    sbml_species_ids = []
    for spec in sbml_model_object.getListOfSpecies():
        if not spec.name == "":
            sbml_species_ids.append(spec)
    names = list(map(lambda s: s.name, sbml_species_ids))
    species_ids = [spec.getId() for spec in sbml_species_ids]
    return dict(zip(names, species_ids))


def handle_sbml_exception() -> str:
    import traceback
    from pprint import pformat
    tb_str = traceback.format_exc()
    error_message = pformat(f"SBML Simulation Error:\n{tb_str}")

    return error_message


def run_tellurium(sbml_fp: str, start, dur, steps):
    simulator = te.loadSBMLModel(sbml_fp)
    floating_species_list = simulator.getFloatingSpeciesIds()
    sbml_species_names = list(get_sbml_species_mapping(sbml_fp).keys())

    try:
        # in the case that the start time is set to a point after the simulation begins
        if start > 0:
            simulator.simulate(0, start)

        # run for the specified time
        result = simulator.simulate(start, dur, steps + 1)
        outputs = {}
        for index, row in enumerate(result.transpose()):
            if not index == 0:
                for i, name in enumerate(floating_species_list):
                    outputs[sbml_species_names[i]] = row

        return outputs
    except:
        error_message = handle_sbml_exception()
        return {"error": error_message}


def run_copasi(sbml_fp: str, start, dur, steps):
    try:
        simulator = load_model(sbml_fp)
        species_info = get_species(model=simulator)
        sbml_ids = list(species_info['sbml_id'])  # matches libsbml and solver ids
        basico_species_names = list(species_info.index)  # sbml species NAMES, as copasi is familiar with the names
        # remove EmptySet reference if applicable
        for _id in basico_species_names:
            if "EmptySet" in _id:
                sbml_ids.remove(_id)
                basico_species_names.remove(_id)
        # set time
        t = np.linspace(start, dur, steps + 1)
        # get outputs
        names = [f'[{name}]' for name in basico_species_names]
        _tc = run_time_course_with_output(output_selection=names, start_time=t[0], duration=t[-1], values=t, model=simulator, update_model=True, use_numbers=True)
        tc = _tc.to_dict()
        results = {}
        for i, name in enumerate(names):
            tc_observable_data = tc.get(name)
            if tc_observable_data is not None:
                results[basico_species_names[i]] = list(tc_observable_data.values())
        return results
    except:
        error_message = handle_sbml_exception()
        return {"error": error_message}


def run_amici(sbml_fp: str, start, dur, steps):
    try:
        sbml_reader = libsbml.SBMLReader()
        sbml_doc = sbml_reader.readSBML(sbml_fp)
        sbml_model_object = sbml_doc.getModel()
        sbml_importer = SbmlImporter(sbml_fp)
        model_id = sbml_fp.split('/')[-1].replace('.xml', '')
        model_output_dir = mkdtemp()
        sbml_importer.sbml2amici(
            model_id,
            model_output_dir,
            verbose=logging.INFO,
            observables=None,
            sigmas=None,
            constant_parameters=None
        )
        # model_output_dir = model_id  # mkdtemp()
        model_module = import_model_module(model_id, model_output_dir)
        amici_model_object: Model = model_module.getModel()
        floating_species_list = list(amici_model_object.getStateIds())
        floating_species_initial = list(amici_model_object.getInitialStates())
        sbml_species_ids = [spec.getName() for spec in sbml_model_object.getListOfSpecies()]
        t = np.linspace(start, dur, steps + 1)
        amici_model_object.setTimepoints(t)
        initial_state = dict(zip(floating_species_list, floating_species_initial))
        set_values = []
        for species_id, value in initial_state.items():
            set_values.append(value)
        amici_model_object.setInitialStates(set_values)
        sbml_species_mapping = get_sbml_species_mapping(sbml_fp)
        method = amici_model_object.getSolver()
        result_data = runAmiciSimulation(solver=method, model=amici_model_object)
        results = {}
        floating_results = dict(zip(
            sbml_species_ids,
            list(map(lambda x: result_data.by_id(x), floating_species_list))
        ))
        results = floating_results

        return results
    except:
        error_message = handle_sbml_exception()
        return {"error": error_message}


SIMULATOR_FUNCTIONS = dict(zip(
    ['amici', 'copasi', 'tellurium'],
    [run_amici, run_copasi, run_tellurium]
))


def sbml_output_stack(spec_name: str, output):
    # 2. in output_stack: return {simname: output}
    stack = {}
    for simulator_name in output.keys():
        spec_data = output[simulator_name].get(spec_name)
        if isinstance(spec_data, str):
            data = None
        else:
            data = spec_data

        stack[simulator_name] = data

    return stack


def get_output_stack(spec_name: str, outputs):
    return sbml_output_stack(spec_name=spec_name, output=outputs)


# def run_sbml_pysces(sbml_fp: str, start, dur, steps):
#     import pysces
#     import os
#     # # model compilation
#     compilation_dir = mkdtemp()
#     sbml_filename = sbml_fp.split('/')[-1]
#     psc_filename = sbml_filename + '.psc'
#     psc_fp = os.path.join(compilation_dir, psc_filename)
#     modelname = sbml_filename.replace('.xml', '')
#     try:
#         # convert sbml to psc
#         pysces.model_dir = compilation_dir
#         pysces.interface.convertSBML2PSC(sbmlfile=sbml_fp, sbmldir=os.path.dirname(sbml_fp), pscfile=psc_fp)
#         # instantiate model from compilation contents
#         with open(psc_fp, 'r', encoding='UTF-8') as F:
#             pscS = F.read()
#             F.close()
#         model = pysces.model(modelname, loader='string', fString=pscS)
#         # run the simulation with specified time params
#         model.sim_start = start
#         model.sim_stop = dur
#         model.sim_points = steps + 1
#         model.Simulate()
#         # get output with mapping of internal species ids to external (shared) species names
#         sbml_species_mapping = get_sbml_species_mapping(sbml_fp)
#         obs_names = list(sbml_species_mapping.keys())
#         obs_ids = list(sbml_species_mapping.values())
#         return {
#             obs_names[i]: model.data_sim.getSimData(obs_id)
#             for i, obs_id in enumerate(obs_ids)
#         }
#     except:
#         error_message = handle_sbml_exception()
#         return {"error": error_message}




