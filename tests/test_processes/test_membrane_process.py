import json
import os

import pytest
from process_bigraph import Process, ProcessTypes, pp
from vivarium.vivarium import Vivarium

from bsp import app_registrar
from bsp.processes.simple_membrane_process import SimpleMembraneProcess

from tests.fixtures.membrane import membrane_composite, membrane_request


CORE: ProcessTypes = app_registrar.core


def validate_process(process: Process, validator_method: str = 'initial_state'):
    method = getattr(process, validator_method)
    assert len(method().keys()) > 0


@pytest.mark.usefixtures('membrane_composite')
def test_membrane_with_vivarium_interface(membrane_composite: dict):
    spec = membrane_composite

    viv = Vivarium(
        processes=CORE.process_registry.registry,
        types=CORE.types(),
        core=CORE,
        document={'state': spec}
    )
    # viv.add_process(
    #     name='membrane',
    #     process_id='simple-membrane-process',
    #     config=spec.get('config'),
    #     # inputs=spec.get('inputs'),
    #     # outputs=spec.get('outputs')
    # )
    print(f'Vivarium:\n{viv}')
    print(f'State: {viv.get_state().get("membrane")}')
    viv.run(3)
    results = viv.get_results()
    print('Output Results:')
    pp(results)



