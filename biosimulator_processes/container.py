import json
import subprocess


def write_config():
    config = {}
    with open('biosimulator_processes/simulators.json', 'w') as fp:
        json.dump(config, fp, indent=4)


def load_config():
    # Load simulator configuration
    with open('biosimulator_processes/simulators.json', 'r') as file:
        return json.load(file)


def add_installations_to_dockerfile(dockerfile_contents: str, config: dict):
    # Iterate over each simulator and add installations for its dependencies
    for simulator in config['simulators']:
        deps = simulator.get('deps', {})
        # Convert dependencies dict to a list of installation commands
        for dep, version in deps.items():
            # For simplicity, assuming all dependencies can be installed via pip
            # This line might need adjustment based on actual package management needs
            dockerfile_contents += f"RUN pip install {dep}{version}\\n"

    # Finish the Dockerfile with any additional setup
    # dockerfile_contents += "    # Add any additional setup here\n"
    return dockerfile_contents


def write_dockerfile(dockerfile_contents: str):
    # Save the Dockerfile
    with open('biosimulator_processes/Dockerfile', 'w') as file:
        file.write(dockerfile_contents)


def exec_container(name: str):
    build_command = f"docker build --platform linux/amd64 {name}_env ."
    subprocess.run(build_command.split())
    run_command = f"docker run --platform linux/amd64 -it -p 8888:8888 {name}_env"
    subprocess.run(run_command.split())


def run(name: str):
    config = load_config()

    base_contents = """RUN apt-get update && apt-get install -y --no-install-recommends \\
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
    && rm -rf /var/lib/apt/lists/*
    """
    dockerfile_contents = add_installations_to_dockerfile(base_contents, config)
    write_dockerfile(dockerfile_contents)
    # exec_container(name)


if __name__ == '__main__':
    run("composite")


