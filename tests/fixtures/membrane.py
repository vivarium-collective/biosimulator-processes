import json
import os

import pytest


def get_fixture(file_dir: str, fname: str) -> str:
    return os.path.join(
        os.path.abspath(
            os.path.dirname(
                os.path.dirname(__file__)
            )
        ),
        file_dir,
        fname
    )


@pytest.fixture
def membrane_composite() -> dict[str, dict[str, float | int] | float | bool]:
    fname = 'membrane_composite.json'
    fp = get_fixture("requests", fname)
    with open(fp, 'r') as f:
        payload = json.load(f)
    return payload


@pytest.fixture
def membrane_request() -> dict[str, dict[str, float | int] | float | bool]:
    fname = 'test_membrane_request.json'
    fp = get_fixture("requests", fname)
    with open(fp, 'r') as f:
        payload = json.load(f)
    return payload
