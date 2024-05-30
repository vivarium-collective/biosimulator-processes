from dataclasses import dataclass
from typing import *
from tempfile import mkdtemp
from abc import ABC, abstractmethod
import os

import requests
import h5py
from process_bigraph import pp, pf

from biosimulator_processes.data_model.service_data_model import RestService, ProjectsQuery, ArchiveFiles, BiosimulationsRunOutputData, BiosimulationsSpeciesOutput


class BiosimulationsRestService(RestService):
    def __init__(self):
        super().__init__()

    @classmethod
    async def _search_source(cls, query: str) -> ProjectsQuery:
        get_all_projects_url = 'https://api.biosimulations.dev/projects'
        headers = {'accept': 'application/json'}
        try:
            all_projects_resp = requests.get(get_all_projects_url, headers=headers)
            all_projects_resp.raise_for_status()
            all_projects = all_projects_resp.json()
            project_ids = [p['id'].lower() for p in all_projects]

            query_result_ids = [project_id for project_id in project_ids if query.lower() in project_id]
            query_result_data = {}
            for project in all_projects:
                project_id = project['id'].lower()
                if project_id in query_result_ids:
                    query_result_data[project_id] = project

            return ProjectsQuery(
                project_ids=query_result_ids,
                project_data=query_result_data)
        except Exception as e:
            print(f'Failed to fetch OMEX archive:\n{e}')

    @classmethod
    def get_project_files(cls, run_id: str, project_name: str = None) -> ArchiveFiles:
        get_files_url = f'https://api.biosimulations.dev/files/{run_id}'
        # get_files_url = f'https://api.biosimulations.dev/results/{run_id}/download'
        headers = {'accept': 'application/json'}
        try:
            files_resp = requests.get(get_files_url, headers=headers)
            run_files = files_resp.json()
            return ArchiveFiles(run_id=run_id, project_name=project_name, files=run_files)
        except Exception as e:
            print(f'Failed to fetch simulation run files:\n{e}')

    @classmethod
    async def fetch_files(cls, query: str) -> ArchiveFiles:
        archive_query = await cls._search_source(query)
        query_results = archive_query.project_ids

        options_menu = dict(zip(list(range(len(query_results))), query_results))
        user_selection = int(input(f'Please enter your archive selection:\n{pf(options_menu)}'))

        selected_project_id = options_menu[user_selection]
        simulation_run_id = archive_query.project_data[selected_project_id]['simulationRun']
        simulation_run_files = cls.get_project_files(simulation_run_id, selected_project_id)
        return simulation_run_files

    @classmethod
    async def extract_data(cls, query: str, save_dir=None) -> str:
        """Return a string representation sbml model from the given query"""
        archive_files = await cls.fetch_files(query)
        get_file_url = f'https://api.biosimulations.dev/files/{archive_files.run_id}'

        model_file_location = [file['location'] for file in archive_files.files if file['location'].endswith('.xml')].pop()
        model_file_resp = requests.get(get_file_url + f'/{model_file_location}/download', headers={'accept': 'application/xml'})

        model_fp = os.path.join(save_dir or mkdtemp(), model_file_location)
        with open(model_fp, 'w') as f:
            f.write(model_file_resp.text)

        return model_file_resp.text

    @classmethod
    def read_report_outputs(cls, report_file_path) -> BiosimulationsRunOutputData:
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
                    output = BiosimulationsSpeciesOutput(dataset_label=label, data=specific_data)
                    outputs.append(output)
                return BiosimulationsRunOutputData(report_path=report_file_path, data=outputs)
            else:
                print(f"Group '{group_path}' not found in the file.")


class SimDataRestService(RestService):
    def __init__(self):
        super().__init__()

    @classmethod
    async def _search_source(cls, query: str) -> ProjectsQuery:
        get_all_projects_url = 'https://api.biosimulations.dev/projects'
        headers = {'accept': 'application/json'}
        try:
            all_projects_resp = requests.get(get_all_projects_url, headers=headers)
            all_projects_resp.raise_for_status()
            all_projects = all_projects_resp.json()
            project_ids = [p['id'].lower() for p in all_projects]

            query_result_ids = [project_id for project_id in project_ids if query.lower() in project_id]
            query_result_data = {}
            for project in all_projects:
                project_id = project['id'].lower()
                if project_id in query_result_ids:
                    query_result_data[project_id] = project

            return ProjectsQuery(
                project_ids=query_result_ids,
                project_data=query_result_data)
        except Exception as e:
            print(f'Failed to fetch OMEX archive:\n{e}')

    @classmethod
    async def _get_files(cls, run_id: str, project_name: str) -> ArchiveFiles:
        get_files_url = f'https://api.biosimulations.dev/files/{run_id}'
        headers = {'accept': 'application/json'}
        try:
            files_resp = requests.get(get_files_url, headers=headers)
            run_files = files_resp.json()
            return ArchiveFiles(run_id=run_id, project_name=project_name, files=run_files)
        except Exception as e:
            print(f'Failed to fetch simulation run files:\n{e}')

    @classmethod
    async def fetch_files(cls, query: str) -> ArchiveFiles:
        archive_query = await cls._search_source(query)
        query_results = archive_query.project_ids

        options_menu = dict(zip(list(range(len(query_results))), query_results))
        user_selection = int(input(f'Please enter your archive selection:\n{pf(options_menu)}'))

        selected_project_id = options_menu[user_selection]
        simulation_run_id = archive_query.project_data[selected_project_id]['simulationRun']
        simulation_run_files = await cls._get_files(simulation_run_id, selected_project_id)
        return simulation_run_files

    @classmethod
    async def extract_data(cls, query: str, save_dir=None) -> str:
        """Return a string representation sbml model from the given query"""
        archive_files = await cls.fetch_files(query)
        get_file_url = f'https://api.biosimulations.dev/files/{archive_files.run_id}'

        model_file_location = [file['location'] for file in archive_files.files if file['location'].endswith('.xml')].pop()
        model_file_resp = requests.get(get_file_url + f'/{model_file_location}/download', headers={'accept': 'application/xml'})

        model_fp = os.path.join(save_dir or mkdtemp(), model_file_location)
        with open(model_fp, 'w') as f:
            f.write(model_file_resp.text)

        return model_file_resp.text



class BiomodelsRestService(RestService):
    pass
