import os
import re
import zipfile as zf
import xml.etree.ElementTree as ET
from tempfile import mkdtemp
from typing import List, Optional, Dict
from pathlib import Path

import h5py
import numpy as np
import requests
import libsbml


class FilePath(Path):
    name: str

    def __init__(self, *args, name: str):
        super().__init__(*args)
        self.name = name


def fetch_biomodel_sbml_file(biomodel_id: str, save_dir: Optional[str] = None) -> FilePath:
    url = f'https://www.ebi.ac.uk/biomodels/search/download?models={biomodel_id}'
    headers = {'accept': '*/*'}
    response = requests.get(url, headers=headers)
    model_filename = f'{biomodel_id}.xml'
    dirpath = save_dir or mkdtemp()  # os.getcwd()
    response_zip_fp = os.path.join(dirpath, 'results.zip')
    if not os.path.exists(response_zip_fp):
        try:
            with open(response_zip_fp, 'wb') as f:
                f.write(response.content)

            with zf.ZipFile(response_zip_fp, 'r') as zipRef:
                zipRef.extract(model_filename, dirpath)

            os.remove(response_zip_fp)
            p = os.path.join(dirpath, model_filename)

            return FilePath(p, name=model_filename)
        except Exception as e:
            print(e)


def read_xyz(xyz_filepath: os.PathLike[str]) -> str:
    lines = []
    with open(xyz_filepath) as f:
        file_contents = f.read().splitlines()
        for i, line in enumerate(file_contents):
            if not file_contents[i] == file_contents[-1]:
                line = f"{line};"
            lines.append(line)
    return " ".join(lines)


def get_sbml_species_mapping(sbml_fp: str) -> dict:
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
        spec_name = spec.name
        if not spec_name:
            spec.name = spec.getId()
        if not spec.name == "":
            sbml_species_ids.append(spec)
    names = list(map(lambda s: s.name, sbml_species_ids))
    species_ids = [spec.getId() for spec in sbml_species_ids]

    return dict(zip(names, species_ids))


def normalize_smoldyn_output_path_in_root(root_fp) -> str | None:
    new_path = None
    for root, dirs, files in os.walk(root_fp):
        for filename in files:
            if filename.endswith('out.txt'):
                original_path = os.path.join(root, filename)
                new_path = os.path.join(root, 'modelout.txt')
                os.rename(original_path, new_path)

    return new_path


def format_smoldyn_configuration(filename: str) -> None:
    config = read_smoldyn_simulation_configuration(filename)
    disable_smoldyn_graphics_in_simulation_configuration(configuration=config)
    return write_smoldyn_simulation_configuration(configuration=config, filename=filename)


def read_smoldyn_simulation_configuration(filename: str) -> List[str]:
    ''' Read a configuration for a Smoldyn simulation

    Args:
        filename (:obj:`str`): path to model file

    Returns:
        :obj:`list` of :obj:`str`: simulation configuration
    '''
    with open(filename, 'r') as file:
        return [line.strip('\n') for line in file]


def write_smoldyn_simulation_configuration(configuration: List[str], filename: str):
    ''' Write a configuration for Smoldyn simulation to a file

    Args:
        configuration
        filename (:obj:`str`): path to save configuration
    '''
    with open(filename, 'w') as file:
        for line in configuration:
            file.write(line)
            file.write('\n')


def disable_smoldyn_graphics_in_simulation_configuration(configuration: List[str]):
    ''' Turn off graphics in the configuration of a Smoldyn simulation

    Args:
        configuration (:obj:`list` of :obj:`str`): simulation configuration
    '''
    for i_line, line in enumerate(configuration):
        if line.startswith('graphics '):
            configuration[i_line] = re.sub(r'^graphics +[a-z_]+', 'graphics none', line)


def unpack_omex_archive(archive_filepath: str, working_dir: str, use_temp: bool = True, write: bool = False) -> str:
    archive_name = archive_filepath.replace('.omex', '')
    unpacking_dirpath = working_dir if not use_temp else mkdtemp()

    if not os.path.exists(unpacking_dirpath) and write:
        os.mkdir(unpacking_dirpath)

    with zf.ZipFile(archive_filepath, 'r') as f:
        f.extractall(path=unpacking_dirpath)

    return unpacking_dirpath


def get_archive_model_filepath(config_model_source: str) -> str:
    return [[os.path.join(root, f) for f in files if f.endswith('.xml') and not f.lower().startswith('manifest')][0] for
            root, _, files in os.walk(config_model_source)][0]


def get_sedml_time_config(sedml_filepath: str) -> Dict:
    # Parse the XML file
    tree = ET.parse(sedml_filepath)
    root = tree.getroot()

    namespace = {'sedml': 'http://sed-ml.org/sed-ml/level1/version3'}

    utc_elements = root.findall('.//sedml:uniformTimeCourse', namespace)

    # Extract data from each uniformTimeCourse element
    utc_data = []
    for utc in utc_elements:
        data = {
            'id': utc.get('id'),
            'initialTime': utc.get('initialTime'),
            'outputStartTime': utc.get('outputStartTime'),
            'outputEndTime': utc.get('outputEndTime'),
            'numberOfPoints': utc.get('numberOfPoints'),
            'algorithm': utc.find('.//sedml:algorithm', namespace).get('kisaoID')
        }
        utc_data.append(data)

    return utc_data[0]


def get_archive_file_location(archive_root: str, filename: str) -> FilePath:
    for f in os.listdir(archive_root):
        if f.endswith(filename):
            path = os.path.join(archive_root, f)
            print(path)
            return FilePath(name=filename, path=path)


def get_model_file_location(archive_root: str) -> FilePath:
    return get_archive_file_location(archive_root, '.xml')


def get_published_t(omex_dirpath: str = None, report_fp: str = None) -> np.ndarray:
    report_fp = get_archive_file_location(
        omex_dirpath, 'reports.h5') if not report_fp else report_fp

    published_outputs = read_report_outputs(report_fp)
    return published_outputs.data[0].data


def read_report_outputs(report_file_path) -> Dict:
    """Read the outputs from all species in the given report file from biosimulations output.
        Args:
            report_file_path (str): The path to the simulation.sedml/report.h5 HDF5 file.
    """
    # TODO: implement auto gen from run id here.
    outputs = []
    with h5py.File(report_file_path, 'r') as f:
        k = list(f.keys())
        group_path = k[0] + '/report'
        if group_path in f:
            group = f[group_path]
            dataset_labels = group.attrs['sedmlDataSetLabels']
            for label in dataset_labels:
                dataset_index = list(dataset_labels).index(label)
                data = group[()]
                specific_data = data[dataset_index]
                output = {"dataset_label": label, "data": specific_data}
                outputs.append(output)

            return {"report_path": report_file_path, "data": outputs}
        else:
            print(f"Group '{group_path}' not found in the file.")