from biosimulator_processes import CORE

from process_bigraph import Step

from biosimulator_processes.api.compare import generate_utc_species_comparison


class UtcComparator(Step):
    config_schema = {
        'simulators': 'list[string]',
        'method': {
            '_default': 'proximity',
            '_type': 'string'
        },
        'include_output_data': {
            '_default': True,
            '_type': 'boolean'
        }
    }

    def __init__(self, config=None, core=None):
        super().__init__(config, core)
        self.method = self.config['method']
        self.simulators = self.config['simulators']

    def inputs(self): 
        port_schema = {
            f'{simulator}_floating_species': 'tree[string]'
            for simulator in self.simulators 
        }
        port_schema['time'] = 'list[float]'
        return port_schema
    
    def outputs(self):
        return {
            'results': 'tree[string]'  # ie: {spec_id: {sim_name: outputarray}}
        }
        
    def update(self, inputs):
        # TODO: more dynamically infer this. Perhaps use libsbml?
        species_names = list(inputs['copasi']['copasi_floating_species'].keys())
        _data = dict(zip(species_names, {}))
        results = {
            'results': _data
        }

        for name in species_names:
            outputs = [inputs[f'{simulator}_floating_species'][name] for simulator in self.simulators]
            comparison = generate_utc_species_comparison(
                outputs=outputs,
                simulators=['copasi', 'amici', 'tellurium'],
                species_name=name)

            comparison_data = comparison.to_dict()
            results['results'][name] = comparison_data

        return results
