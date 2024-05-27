from typing import *
from tempfile import mkdtemp
from dataclasses import dataclass
import requests
import zipfile as zf
import json
import os

from biosimulator_processes.data_model import _BaseClass


@dataclass
class FilePath(_BaseClass):
    name: str
    path: str


def get_archive_file_location(archive_root: str, filename: str) -> FilePath:
    for f in os.listdir(archive_root):
        if f.endswith(filename):
            path = os.path.join(archive_root, f)
            print(path)
            return FilePath(name=filename, path=path)


def get_model_file_location(archive_root: str) -> FilePath:
    return get_archive_file_location(archive_root, '.xml')


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
            num_points = report['points']
            reported_time_vals = report['values'][0]['value']
            time_indices = list(reported_time_vals.keys())
            time_values = list(reported_time_vals.values())
            print(time_values)
            end_time_index = float(time_values[-1])
            return {
                'duration':  int(time_indices[-1]),  # int(end_time_index),
                'step_size': time_values[-1] / end_time_index,
                'num_steps': int(end_time_index),  # int(time_indices[-1])
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
