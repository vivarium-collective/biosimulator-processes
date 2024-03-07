import json


def write_dockerfile(dockerfile_contents: str, out_path: str):
    """
        Args:
            dockerfile_contents:`str`: content to write to Dockerfile
            out_path:`str`: path to save the Dockerfile

    """
    with open(out_path, 'w') as file:
        file.write(dockerfile_contents)


def write_config():
    config = {}
    with open('biosimulator_processes/simulators.json', 'w') as fp:
        json.dump(config, fp, indent=4)


def load_config():
    # Load simulator configuration
    with open('biosimulator_processes/simulators.json', 'r') as file:
        return json.load(file)
