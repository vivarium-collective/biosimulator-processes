from typing import *
import requests
import zipfile as zf
import os


def fetch_sbml_file(biomodel_id: str, save_dir: Optional[str] = None) -> str:
    url = f'https://www.ebi.ac.uk/biomodels/search/download?models={biomodel_id}'
    headers = {'accept': '*/*'}
    response = requests.get(url, headers=headers)
    model_filename = f'{biomodel_id}.xml'
    dirpath = save_dir or os.getcwd()
    response_fp = os.path.join(dirpath, 'results.zip')
    if not os.path.exists(response_fp):
        with open(response_fp, 'wb') as f:
            f.write(response.content)

        with zf.ZipFile(response_fp, 'r') as zipRef:
            zipRef.extract(model_filename, dirpath)

    return os.path.join(dirpath, model_filename)
