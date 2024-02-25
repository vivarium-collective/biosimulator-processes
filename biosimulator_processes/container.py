import json
import os
import subprocess
import tempfile
import docker

'''unix:///var/run/docker.sock

instantiate DockerClient'''


CLIENT = docker.DockerClient(
    base_url='unix:///var/run/docker.sock'
)

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


def add_simulator_installations(base_path: str, config: dict):
    """
        Args:
            base_path:`str`: path to the base dockerfile on which to append installations.
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
    # TODO: automate mapping simulators to poetry.lock: ie: simulators arg that searches the lock file
    with open(base_path, 'r') as fp:
        dockerfile_contents = fp.read()
        for simulator in config['simulators']:
            deps = simulator.get('deps', {})
            for dep, version in deps.items():
                # dockerfile_contents += f"RUN pip install {dep}{version}\n"
                dockerfile_contents += f"RUN poetry add {dep}{version}\n"

        # common entrypoint used by all processes
        dockerfile_contents += 'ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]'
    return dockerfile_contents


def add_installations_to_dockerfile(dockerfile_contents: str, config: dict):
    """
        Args:
            dockerfile_contents:`str`: starting content for your dockerfile.
            config:`dict`: simulator configuration containing simulator version and dependencies. Derived
            possibly from poetry.lock. For example:

            {
              "simulators": [
                {
                  "name": "tellurium",
                  "version": "2.2.10",
                  "description": "Tellurium: An biological modeling environment for Python",
                  "optional": false,
                  "python-versions": "*",
                  "files": [
                    {
                      "file": "tellurium-2.2.10-py3-none-any.whl",
                      "hash": "sha256:078dbe5beeef49cc8caa9f626cb9c8e568752ecfaff3370acd32be123d6e24ae"
                    }
                  ],
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
    # Iterate over each simulator and add installations for its dependencies
    for simulator in config['simulators']:
        deps = simulator.get('deps', {})
        # Convert dependencies dict to a list of installation commands
        for dep, version in deps.items():
            # For simplicity, assuming all dependencies can be installed via pip
            # This line might need adjustment based on actual package management needs
            dockerfile_contents += f"RUN pip install {dep}{version}\n"

    # common entrypoint used by all processes
    dockerfile_contents += 'ENTRYPOINT ["poetry", "run", "jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]'
    return dockerfile_contents


def write_dockerfile(dockerfile_contents: str, path: str = 'biosimulator_processes/Dockerfile'):
    # Save the Dockerfile
    with open(path, 'w') as file:
        file.write(dockerfile_contents)


def exec_container(name: str):
    build_command = f"docker buildx build --platform linux/amd64 {name}_env ."
    subprocess.run(build_command.split())
    run_command = f"docker run --platform linux/amd64 -it -p 8888:8888 {name}_env"
    subprocess.run(run_command.split())


def build_image(name: str, p: str = '.'):
    return CLIENT.images.build(
        path=p,
        tag=name)
        

def execute_container(img_name: str):
    container_dir = tempfile.mkdtemp()
    img = build_image(img_name)
    CLIENT.containers.run(img.id)
    

def run(name: str):
    config = load_config()

    base_contents = f"""
FROM ubuntu:latest \\
RUN apt-get update && apt-get install -y --no-install-recommends \\
                       python3 \\
                       python3-pip \\
                       build-essential \\
                       libncurses5 \\
                       cmake \\
                       make \\
                       libx11-dev \\
                       libc6-dev \\
                       libx11-6 \\
                       libc6 \\
                       gcc \\
                       swig \\
                       pkg-config \\
                       curl \\
                       tar \\
                       libgl1-mesa-glx \\
                       libice6 \\
                       libpython3.10 \\
                       wget \\
                       && rm -rf /var/lib/apt/lists/*"""
    # dockerfile_contents = add_installations_to_dockerfile(base_contents, config)

    dockerfile_contents = add_simulator_installations(
        base_path='Dockerfile-base',
        config=config
    )

    container_dir = tempfile.mkdtemp()
    write_dockerfile(dockerfile_contents, path='Dockerfile')
    execute_container(name)


if __name__ == '__main__':
    run("composite")


