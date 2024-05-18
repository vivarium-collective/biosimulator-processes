from dataclasses import dataclass
from typing import *
from tempfile import mkdtemp
from abc import ABC, abstractmethod
import os

import requests
from process_bigraph import pp, pf

from biosimulator_processes.data_model.service_data_model import RestService, ProjectsQuery, ArchiveFiles


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
