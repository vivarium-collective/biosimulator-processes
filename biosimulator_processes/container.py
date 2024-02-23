import json
import subprocess


def load_config():
    # Load simulator configuration
    with open('simulators.json', 'r') as file:
        return json.load(file)

def add_installations_to_dockerfiile(dockerfile_contents: str):
    # Add installations for each simulator and its dependencies
    for simulator in config['simulators']:
        # Example: Assuming dependencies can be installed via apt-get for simplicity
        deps = ' '.join(simulator['deps'])
        dockerfile_contents += f"    {deps} \\\n"

    # Finish the Dockerfile
    dockerfile_contents += """
    # Add any additional setup here
    """
    return dockerfile_contents


def write_dockerfile(dockerfile_contents: str):
    # Save the Dockerfile
    with open('Dockerfile', 'w') as file:
        file.write(dockerfile_contents)


def exec_container(name: str):
    # Build the Docker image
    subprocess.run(["docker", "build", "-t", "simulator_env", "."])
    # Run the Docker container
    subprocess.run(["docker", "run", "-d", "--name", "simulator_instance", f"{name}"])


def run(name: str):
    config = load_config()

    base_contents = """
    FROM ubuntu:latest
    RUN apt-get update && apt-get install -y \\
    """
    dockerfile_contents = add_installations_to_dockerfiile(base_contents)
    write_dockerfile(dockerfile_contents)
    exec_container(name)


