from typing import Any

from vivarium import Vivarium

from bsp import app_registrar


CORE = app_registrar.core


def process_request(spec: dict, duration: int) -> list[dict[str, Any]]:
    viv = Vivarium(
        processes=CORE.process_registry.registry,
        types=CORE.types(),
        core=CORE,
        document={'state': spec}
    )
    if 'emitter' not in viv.get_state().keys():
        viv.add_emitter()

    viv.run(duration)
    return viv.get_results()
