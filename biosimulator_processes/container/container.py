import json
import os
import subprocess
import tempfile
import docker


CLIENT = docker.DockerClient(
    base_url='unix:///var/run/docker.sock'
)


def add_simulator_installations(config: dict):
    """
        Args:
            # base_path:`str`: path to the base dockerfile on which to append installations.
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
    
    base_path = 'Dockerfile-base'
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

    dockerfile_contents = add_simulator_installations(
        base_path='Dockerfile-base',
        config=config
    )

    container_dir = tempfile.mkdtemp()
    write_dockerfile(dockerfile_contents, path='Dockerfile')
    execute_container(name)


if __name__ == '__main__':
    run("composite")


