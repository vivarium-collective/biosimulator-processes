![PYPI Deployment](https://github.com/vivarium-collective/biosimulator-processes/actions/workflows/cd.yaml/badge.svg)

# BioSimulator Processes

Core implementations of `process-bigraph.composite.Process()` and `process-bigraph.composite.Step()` aligning with BioSimulators simulation 
tools. A complete environment with version-controlled dependencies already installed is available as a Docker container on GHCR.


## Installation:
### A. Via the Python Package Index. You may download BioSimulator Processes with: 

         pip install biosimulator-processes

We recommend using an environment/package manager like UV.


## Simulator process set-up and installation
This project implements the `process_bigraph.Process()` interface around several "low-level" simulator python APIs. The error-handling in `bsp` is set in such a way that if a particular simulator is not installed, 
then the corresponding process implementation for it will not be loaded into memory. Consider the following list of "optional" dependencies, convering the entire range of available implementations:

```python
cobra = ["cobra>=0.29.1"]
copasi = ["copasi-basico>=0.83"]
dev = [
    "mypy>=1.15.0",
    "pre-commit>=4.1.0",
    "pytest>=8.3.5",
    "pytest-cov>=6.0.0",
    "ruff>=0.11.0",
]
docs = [
    "griffe>=1.6.2",
    "mkdocs>=1.6.1",
    "mkdocs-material>=9.6.9",
    "mkdocstrings[python]>=0.29.0",
    "nbsphinx>=0.9.7",
    "sphinx>=8.1.3",
    "sphinx-rtd-theme>=3.0.2",
]
membrane = ["pymem3dg>=0.0.7"]
tellurium = ["tellurium>=2.2.10"]
vcell = ["pyvcell>=0.0.1"]
```

## Interaction via a container available on `ghcr`:


   1. Ensure that the Docker Daemon is running. Most users do this by opening the Docker Desktop application.
   2. Pull the image from `ghcr.io`:
         
            docker pull ghcr.io/vivarium-collective/biosimulator-processes:latest
   
   3. If there are any "dangling" or already-running jupyter servers running on your machine, the `docker run` command will not properly work. Run the following and close any servers already running, if necessary:
   
            jupyter server list && jupyter server stop

   4. Run the image, ensuring that the running of the container is platform-agnostic:
   
            docker run --platform linux/amd64 -it -p 8888:8888 ghcr.io/vivarium-collective/biosimulator-processes:latest


   **MAC USERS**: Please note that an update of XCode may be required for this to work on your machine.
   
   As an alternative, there is a helper script that does this docker work and more. To use this script:
   
      1. Add the appropriate permissions to the file:
            
               chmod +x ./scripts/run-docker.sh
   
      2. Run the script:
   
               ./scripts/run-docker.sh


### Quick Start Example:
TODO: copy this from the prompter demo

### A NOTE FOR DEVELOPERS:
This tooling implements version control for dynamically-created composite containers through
`conda`. The version control for content on the Python Package Index is performed by 
`setup.py`. Also, the PyTest configuration resides within `./pyproject.toml` at the root of this repository.
