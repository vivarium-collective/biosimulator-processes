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


def parse_simulator_deps(deps):
    """Parse dependencies, handling conditional dependencies."""
    parsed_deps = {}
    for dep in deps:
        if isinstance(dep, str):
            # Simple dependency
            if " " in dep:
                name, version = dep.split(" ", 1)
            else:
                name, version = dep, "*"
            parsed_deps[name] = version
        elif isinstance(dep, dict):
            # Conditional dependency
            for name, info in dep.items():
                if "version" in info:
                    parsed_deps[name] = {
                        "version": info["version"],
                        "markers": info.get("markers", "")
                    }
    return parsed_deps


def get_simulator(sim: str):
    # Load the poetry.lock file
    with open('poetry.lock') as file:
        lock_data = toml.load(file)

    simulators = []

    # Iterate through the packages in the poetry.lock file
    for package in lock_data.get('package', []):
        if package['name'] == sim:
            # Found the simulator, now get its dependencies
            deps = parse_simulator_deps(package.get('dependencies', []))
            simulators.append({
                "name": package['name'],
                "version": package['version'],
                "deps": deps
            })
            break

    return {"simulators": simulators}

# Example usage
simulator_info = get_simulator("tellurium")
print(simulator_info)
