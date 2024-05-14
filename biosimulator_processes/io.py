from typing import *
from tempfile import mkdtemp
import requests
import zipfile as zf
import os


async def fetch_sbml_file(biomodel_id: str, save_dir: Optional[str] = None) -> str:
    """return the filepath of a SBML file that has been uploaded to `save_dir` which
        was retrieved from `biomodel_id` and the biomodels rest api.
    """
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
            return os.path.join(dirpath, model_filename)
        except Exception as e:
            print(e)
