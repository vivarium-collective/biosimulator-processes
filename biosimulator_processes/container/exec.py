import toml
from typing import *


def get_simulators(*sims: str):
    """Get specified simulator installation information including required dependencies
        and format as a dictionary. This dictionary is used as configuration for the dynamic
        creation of containers.

        Args:
              sims:`args, str`: names of the simulators to be included within the
                container.

    """
    with open('biosimulator_processes/container-assets/poetry.lock') as file:
        lock_data = toml.load(file)

    simulators = []
    for sim in sims:
        for package in lock_data.get('package', []):
            if package['name'] == sim:
                simulators.append({
                    "name": package['name'],
                    "version": package['version'],
                    "deps": package.get('dependencies', {}),
                    "extras": package.get('extras', {})
                })
                break

    return {"simulators": simulators}
