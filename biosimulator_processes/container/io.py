import json
import toml


def write_config():
    config = {}
    with open('biosimulator_processes/simulators.json', 'w') as fp:
        json.dump(config, fp, indent=4)


def load_config():
    # Load simulator configuration
    with open('biosimulator_processes/simulators.json', 'r') as file:
        return json.load(file)


def find_package_info(package: str):
    # TODO: Finish this
    package = {}
    with open('poetry.lock', 'r') as f:
        pass


def write_dockerfile(dockerfile_contents: str, path: str = 'biosimulator_processes/Dockerfile'):
    # Save the Dockerfile
    with open(path, 'w') as file:
        file.write(dockerfile_contents)

