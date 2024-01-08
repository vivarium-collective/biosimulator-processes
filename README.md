# biosimulator-processes 


Core implementations of `process-bigraph.composite.Process()` aligning with BioSimulators simulator
tools.


## Installation

The easiest way to download this tool is via the Python Package Index. You may download
core-processes with: 

    pip install biosimulator-processes

We recommend using an environment/package manager [like Conda](https://conda.io/projects/conda/en/latest/index.html) to 
install the dependencies required for your use.

 Most of the direct UI content for this tooling will be in the form of a jupyter notebook.

### Using `biosimulator_processes.smoldyn_process.SmoldynProcess()`: 

#### Mac Users PLEASE NOTE: 
Due to the multi-lingual nature of Smoldyn, which is primarily 
developed in C++, the installation process for utilizing 
the `SmoldynProcess` process implementation requires separate handling. This is particularly 
relevant for macOS and Windows users, where setting up the Python bindings can be more complex.

For your convienience, we have created an installation shell script that will install the correct distribution of 
Smoldyn based on your Mac processor along with the codebase of this repo. To install Smoldyn and this repo on your 
Mac, please adhere to the following instructions:

1. Clone this repo from Github:

        git clone https://github.com/vivarium-collective/biosimulator-processes.git

2. Provide adminstrative access to the `scripts` directory within the cloned repo:

        cd biosimulator-processes 
        chmod +x scripts 

3. Look for the install-with-smoldyn-for-mac-<YOUR MAC PROCESSOR> shell script where <YOUR MAC PROCESSOR> corresponds 
    to your machine's processor:

        ls scripts 

4. Run the appropriate shell script (for example, using mac silicon):

        scripts/install-with-smoldyn-for-mac-silicon.sh 

### Quick Start Example:
#### TODO: Add quickstart example of instance declarations.


## TODO: Add DatabaseEmitter to this README


