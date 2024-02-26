import toml
import os
from typing import *
from docker import DockerClient


CLIENT = DockerClient(base_url='unix:///var/run/docker.sock')


def get_simulators(simulators: List[str]):
    """Get specified simulator installation information including required dependencies
        and format as a dictionary. This dictionary is used as configuration for the dynamic
        creation of containers.

        Args:
              simulators:`List[str]`: names of the simulators to be included within the
                container.

    """
    with open('biosimulator_processes/container-assets/poetry.lock') as file:
        lock_data = toml.load(file)

    simulators = []
    for sim in simulators:
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


def generate_dockerfile_contents(config: dict) -> str:
    """Generate contents to be written out to a Dockerfile derived from the base Dockerfile.

        Args:
            config:`dict`: a dictionary specifying simulator versions and their dependencies. The schema for
                 this dictionary should be (for example):

            {
              "simulators": [
                {
                  "name": "tellurium",
                  "version": "2.2.10",
                  "deps": {
                    "antimony": ">=2.12.0",
                    "appdirs": ">=1.4.3",
                    "ipykernel": ">=4.6.1",
                    "ipython": "*",
                    "jinja2": ">=3.0.0",
                    "jupyter-client": ">=5.1.0",
                    "jupyter-core": ">=4.3.0",
                    "libroadrunner": ">=2.1",
                    "matplotlib": ">=2.0.2",
                    "numpy": ">=1.23",
                    "pandas": ">=0.20.2",
                    "phrasedml": {
                      "version": ">=1.0.9",
                      "markers": "platform_machine != \"arm64\""
                    },
                    "plotly": ">=2.0.12",
                    "pytest": "*",
                    "python-libcombine": ">=0.2.2",
                    "python-libnuml": ">=1.0.0",
                    "python-libsbml": ">=5.18.0",
                    "python-libsedml": ">=2.0.17",
                    "requests": "*",
                    "rrplugins": {
                      "version": ">=2.1",
                      "markers": "platform_system == \"Windows\""
                    },
                    "scipy": ">=1.5.1"
                  }
                },
    """

    base_path = 'biosimulator_processes/container-assets/Dockerfile-base'
    # TODO: automate mapping simulators to poetry.lock: ie: simulators arg that searches the lock file
    with open(base_path, 'r') as fp:
        dockerfile_contents = fp.read()
        for simulator in config['simulators']:
            # copy the appropriate process files
            name = simulator['name']
            if name == 'copasi-basico':
                name = 'copasi'
            dockerfile_contents += f"COPY ./biosimulator_processes/{simulator['name']}_process.py"

            deps = simulator.get('deps', {})
            for dep, version in deps.items():
                # dockerfile_contents += f"RUN pip install {dep}{version}\n"
                dockerfile_contents += f"RUN poetry add {dep}{version}\n"

        # common entrypoint used by all processes
        dockerfile_contents += 'ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]'
    return dockerfile_contents


def build_image(name: str, p: str = '.'):
    return CLIENT.images.build(
        path=p,
        tag=name)


def execute_container(img_name: str):
    img = build_image(img_name)
    CLIENT.containers.run(img.id)


def run(simulators: List[str]):
    config = get_simulators(simulators)
    dockerfile_contents = generate_dockerfile_contents(config)
    write_dockerfile(dockerfile_contents, path='Dockerfile')
    execute_container(name)


if __name__ == '__main__':
    run("composite")


