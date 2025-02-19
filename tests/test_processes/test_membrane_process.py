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
    config = payload.get('spec').get('membrane').get('config')
    config.pop('geometry')
    config['mesh_file'] = get_mesh_file()

    return config


@pytest.mark.usefixtures('membrane_config')
class TestMembraneProcess:
    def test_membrane_process_from_config(self, membrane_config: dict):
        process = SimpleMembraneProcess(config=membrane_config, core=app_registrar.core)
        print(f'Created the process:\n{process.initial_state()}')
        assert process is not None
        assert hasattr(process, "update")
