import json
import os

import pytest

from bsp.processes.simple_membrane_process import SimpleMembraneProcess
from bsp import app_registrar


def get_mesh_file() -> str:
    fname = 'oblate.ply'
    fp = os.path.join(
        os.path.abspath(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        "fixtures",
        "sample_meshes",
        fname
    )
    assert os.path.exists(fp)
    return fp


@pytest.fixture
def membrane_config() -> dict[str, dict[str, float | int] | float | bool]:
    fname = 'membrane_composite.json'
    fp = os.path.join(
        os.path.abspath(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        "fixtures",
        fname
    )
    with open(fp, 'r') as f:
        payload = json.load(f)
    return payload.get('membrane').get('config')


@pytest.fixture
def membrane_request() -> dict[str, dict[str, float | int] | float | bool]:
    fname = 'test_membrane_request.json'
    fp = os.path.join(
        os.path.abspath(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        "fixtures",
        fname
    )
    with open(fp, 'r') as f:
        payload = json.load(f)
    return payload.get('spec').get('membrane')


@pytest.mark.usefixtures('membrane_config')
def test_membrane_process_from_config(membrane_config: dict):
    membrane = SimpleMembraneProcess(config=membrane_config, core=app_registrar.core)
    print(f'Created membrane process with initial state: {membrane.initial_state()}')

