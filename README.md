# BioSimulator Processes


Core implementations of `process-bigraph.composite.Process()` aligning with BioSimulators simulation 
tools. A complete environment with version-controlled dependencies already installed is available as a Docker container on GHCR.


## Installation

There are two primary methods of interaction with `biosimulator-processes`:

### A container available on `ghcr`:


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

### The Python Package Index. You may download BioSimulator Processes with: 

         pip install biosimulator-processes

We recommend using an environment/package manager [like Conda](https://conda.io/projects/conda/en/latest/index.html) if downloading from PyPI to 
install the dependencies required for your use. Most of the direct UI content for this tooling will be in the form of
a jupyter notebook. The installation for this notebook is provided below.

### Using `biosimulator_processes.smoldyn_process.SmoldynProcess()`: 

#### Mac Users PLEASE NOTE: 

##### **Amici**
You most likely have to install/update `swig` with `brew`, among other possible requirements. Please refer to the
[Amici Python Installation Documentation](https://amici.readthedocs.io/en/latest/python_installation.html) for 
more information.

##### **Smoldyn**
Due to the multi-lingual nature of Smoldyn, which is primarily 
developed in C++, the installation process for utilizing 
the `SmoldynProcess` process implementation requires separate handling. This is particularly 
relevant for macOS and Windows users, where setting up the Python bindings can be more complex.

For your convienience, we have created an installation shell script that will install the correct distribution of 
Smoldyn based on your Mac processor along with the codebase of this repo. To install Smoldyn and this repo on your 
Mac, please adhere to the following instructions:

1. Clone this repo from Github:

        git clone https://github.com/biosimulators/biosimulator-processes.git

2. Provide adminstrative access to the `scripts` directory within the cloned repo:

        cd biosimulator-processes

3. Look for the install-with-smoldyn-for-mac-<YOUR MAC PROCESSOR> shell script where <YOUR MAC PROCESSOR> corresponds 
    to your machine's processor:

        ls scripts | grep <YOUR MAC PROCESSOR>
        chmod +x ./scripts/install-with-smoldyn-for-mac-<YOUR MAC PROCESSOR>

4. Run the appropriate shell script (for example, using mac silicon):

        scripts/install-with-smoldyn-for-mac-silicon.sh

### Quick Start Example:
TODO: copy this from the prompter demo

### A NOTE FOR DEVELOPERS:
This tooling implements version control for dynamically-created composite containers through
`poetry`. The version control for content on the Python Package Index is performed by 
`setup.py`. Also, the PyTest configuration resides within `./pyproject.toml` at the root of this repository.
