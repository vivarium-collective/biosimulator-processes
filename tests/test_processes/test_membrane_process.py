import json
import os

import pytest

from bsp.processes.simple_membrane_process import SimpleMembraneProcess
from bsp import app_registrar


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
    return payload.get('spec').get('membrane').get('config')


def test_membrane_process(membrane_config: dict):
    process = SimpleMembraneProcess(config=membrane_config, core=app_registrar.core)
    assert process is not None
    assert hasattr(process, "update")

