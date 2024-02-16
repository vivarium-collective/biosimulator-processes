from biosimulator_processes.smoldyn_process import SmoldynProcess


instance = {'smoldyn': {'_type': 'process',
  'address': 'local:smoldyn',
  'config': {'model_filepath': 'biosimulator_processes/model_files/minE_model.txt',
   'animate': None},
  'inputs': {'species_counts': ['species_counts_store'],
   'molecules': ['molecules_store']},
  'outputs': {'species_counts': ['species_counts_store'],
   'molecules': ['molecules_store']}},
 'emitter': {'_type': 'step',
  'address': 'local:ram-emitter',
  'config': {'emit': {'species_counts': 'tree[any]',
    'molecules': 'tree[any]'}},
  'inputs': {'species_counts': ['species_counts_store'],
   'molecules': ['molecules_store']}}}

config = instance.get('smoldyn').get('config')

process = SmoldynProcess(config)

inputData = {
  'species_counts': {
    'MinDMinE': 0,
    'MinD_ADP': 23,
    'MinD_ATP': 23423,
    'MinE': 33
    },
    'molecules': {
       name: {
         'coordinates': [0.0, 0.0, 0.0],
         'species_id': process.species_names[i],
         'state': 0
       }
       for i, name in enumerate(process.molecule_ids)
    }
}


def main():
    results = []
    results.append(process.initial_state())
    for i, r in enumerate(results):
        if i == 0:
            i += 1
        result = process.update(results[i - 1], i)
        results.append(result)
        print(f'ITERATION STORED AT {i}')
        print()
    print('THE RESULTS:')
    print(results)


# main()
