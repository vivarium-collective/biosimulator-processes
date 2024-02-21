# biosimulator-processes 


Core implementations of `process-bigraph.composite.Process()` aligning with BioSimulators simulator
tools. A Docker container complete with all required dependencies is available as part of the features of this tooling.


## Installation

The easiest way to download this tool is via the Python Package Index. You may download
core-processes with: 

    pip install biosimulator-processes

We recommend using an environment/package manager [like Conda](https://conda.io/projects/conda/en/latest/index.html) to 
install the dependencies required for your use. Most of the direct UI content for this tooling will be in the form of
a jupyter notebook. The installation for this notebook is provided below.

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

        git clone https://github.com/biosimulators/biosimulator-processes.git

2. Provide adminstrative access to the `scripts` directory within the cloned repo:

        cd biosimulator-processes

3. Look for the install-with-smoldyn-for-mac-<YOUR MAC PROCESSOR> shell script where <YOUR MAC PROCESSOR> corresponds 
    to your machine's processor:

        ls scripts | grep <YOUR MAC PROCESSOR>
        chmod +x ./scripts/install-with-smoldyn-for-mac-<YOUR MAC PROCESSOR>

4. Run the appropriate shell script (for example, using mac silicon):

        scripts/install-with-smoldyn-for-mac-silicon.sh

## Accessing the containerized notebook/builder:

One of the primary features of this tooling is a docker container complete with all dependencies along with scripts
to interact/run the container. The image is available on `ghcr`. To access the container, complete the following steps:

1. Ensure that the Docker Daemon is running. Most users do this by opening the Docker Desktop application.
2. Pull the image from `ghcr.io`:
         
         docker pull ghcr.io/biosimulators/biosimulator-processes:0.0.1

3. Run the image, ensuring that the running of the container is platform-agnostic:

         docker run --platform linux/amd64 -it -p 8888:8888 ghcr.io/biosimulators/biosimulator-processes:0.0.1

As an alternative, there is a helper script that does this and more. To use this script:

1. Add the appropriate permissions to the file:
         
         chmod +x ./scripts/run-docker.sh

2. Run the script:

         ./scripts/run-docker.sh


### Quick Start Example:

Composing, running, and viewing the results of a composite simulation can be achieved in as little as 4 steps. 
In this example, we use the `CopasiProcess` implementation to compose a sbml-based simulation.

1. Define the composite instance according to the `process_bigraph.Composite` API and relative process
   implementation (in this case the `CopasiProcess`). Each instance of the Copasi process requires the specification
   of an SBML model file, which is specified in the inner key, `'config'` :
         
         from process_bigraph import Composite, pf
   
         instance = {
              'copasi': {
                  '_type': 'process',
                  'address': 'local:copasi',
                  'config': {
                      'model_file': 'biosimulator_processes/tests/model_files/Caravagna2010.xml'
                  },
                  'inputs': {
                      'floating_species': ['floating_species_store'],
                      'model_parameters': ['model_parameters_store'],
                      'time': ['time_store'],
                  },
                  'outputs': {
                      'floating_species': ['floating_species_store'],
                      'time': ['time_store'],
                  }
              },
              'emitter': {
                  '_type': 'step',
                  'address': 'local:ram-emitter',
                  'config': {
                      'ports': {
                          'inputs': {
                              'floating_species': 'tree[float]',
                              'time': 'float'
                          },
                          'output': {
                              'floating_species': 'tree[float]',
                              'time': 'float'
                          }
                      }
                  },
                  'inputs': {
                      'floating_species': ['floating_species_store'],
                      'time': ['time_store']
                  }
              }
         }

   As you can see, each instance definition is expected to have the following key heirarchy:
         
         instance[
            <INSTANCE-NAME>['_type', 'address', 'config', 'inputs', 'outputs'], 
            ['emitter']['_type', 'address', 'config', 'inputs', 'outputs']
         ]
   Each instance requires at least one process and one emitter. Usually, there may be multiple processes and just 
      one emitter, thereby sharing memory amongst the chained processes.
   
   Both `<INSTANCE-NAME>` and `'emitter'` share the same inner keys. Here, pay close attention to how the `'address'`
      is set for both the instance name and emitter.

2. Create a `process_bigraph.Composite` instance:

         workflow = Composite({
            'state': instance
         })

3. Run the composite instance which is configured by the `instance` that we defined:
    
         workflow.run(10)

4. Gather and pretty print results:
       
         results = workflow.gather_results()
         print(f'RESULTS: {pf(results)}')


A simplified view of the above script:


         from process_bigraph import Composite, pf
   
         >> instance = {
                 'copasi': {
                     '_type': 'process',
                     'address': 'local:copasi',
                     'config': {
                         'model_file': 'biosimulator_processes/tests/model_files/Caravagna2010.xml'
                     },
                     'inputs': {
                         'floating_species': ['floating_species_store'],
                         'model_parameters': ['model_parameters_store'],
                         'time': ['time_store'],
                     },
                     'outputs': {
                         'floating_species': ['floating_species_store'],
                         'time': ['time_store'],
                     }
                 },
                 'emitter': {
                     '_type': 'step',
                     'address': 'local:ram-emitter',
                     'config': {
                         'ports': {
                             'inputs': {
                                 'floating_species': 'tree[float]',
                                 'time': 'float'
                             },
                             'output': {
                                 'floating_species': 'tree[float]',
                                 'time': 'float'
                             }
                         }
                     },
                     'inputs': {
                         'floating_species': ['floating_species_store'],
                         'time': ['time_store']
                     }
                 }
            }

         >> workflow = Composite({
               'state': instance
            })

         >> workflow.run(10)
         >> results = workflow.gather_results()
         >> print(f'RESULTS: {pf(results)}')
