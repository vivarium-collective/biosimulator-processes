from process_bigraph import Composite, pf


def test_process():
    # 1. Define the sim state schema:
    initial_sim_state = {
        'copasi': {
            '_type': 'process',
            'address': 'local:copasi',
            'config': {
                'model_file': 'biosimulator_processes/tests/model_files/Caravagna2010.xml'
            },
            'inputs': {
                'floating_species': ['floating_species_store'],
                # 'boundary_species': ['boundary_species_store'],
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                # 'compartments': ['compartments_store'],
                # 'parameters': ['parameters_store'],
                # 'stoichiometries': ['stoichiometries_store']
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

    # 2. Make the composite:
    workflow = Composite({
        'state': initial_sim_state
    })

    # 3. Run the composite workflow:
    workflow.run(10)

    # 4. Gather and pretty print results
    results = workflow.gather_results()
    print(f'RESULTS: {pf(results)}')

