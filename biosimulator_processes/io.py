from typing import *
from tempfile import mkdtemp
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import requests
import zipfile as zf
from zipfile import ZipFile
import json
import os

import h5py
import numpy as np
from biosimulator_processes.data_model import _BaseClass
from biosimulator_processes.data_model.service_data_model import BiosimulationsRunOutputData, BiosimulationsReportOutput


@dataclass
class FilePath(_BaseClass):
    name: str
    path: str


def unpack_omex_archive(archive_filepath: str, working_dir: str) -> str:
    archive_name = archive_filepath.replace('.omex', '')
    unpacking_dirpath = os.path.join(working_dir, archive_name)
    if not os.path.exists(unpacking_dirpath):
        os.mkdir(unpacking_dirpath)
    with ZipFile(archive_filepath + '.omex', 'r') as f:
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
        omex_dirpath, 'reports.h5').path if not report_fp else report_fp

    published_outputs = read_report_outputs(report_fp)
    return published_outputs.data[0].data


def parse_expected_timecourse_config(
        archive_root: str = None,
        expected_results_fp: str = None
        ) -> Dict[str, Union[int, float]]:
    source = expected_results_fp or os.path.join(archive_root, 'expected-results.json')
    with open(source, 'r') as fp:
        expected = json.load(fp)

    expected_reports = expected['expectedReports']
    for report in expected_reports:
        report_id = report['id'].lower()
        if 'report' in report_id:
            num_points = int(report['points'][0])
            reported_time_vals = report['values'][0]['value']
            time_indices = list(reported_time_vals.keys())
            time_values = list(reported_time_vals.values())
            print(time_values)
            end_time_index = float(time_values[-1])
            return {
                'duration':  int(end_time_index),
                'step_size': time_values[-1] / end_time_index,
                'num_steps': num_points  # int(end_time_index),  # int(time_indices[-1])
            }


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

            return FilePath(name=model_filename, path=p)
        except Exception as e:
            print(e)


# OUTPUTS
def read_report_outputs(report_file_path) -> BiosimulationsRunOutputData:
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
                output = BiosimulationsReportOutput(dataset_label=label, data=specific_data)
                outputs.append(output)
            return BiosimulationsRunOutputData(report_path=report_file_path, data=outputs)
        else:
            print(f"Group '{group_path}' not found in the file.")
