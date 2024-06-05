from process_bigraph import Step 

from biosimulator_processes.api.compare import generate_comparison


class Comparator(Step):
    config_schema = {
        'simulators': 'list[string]',
        'method': {
            '_default': 'proximity',
            '_type': 'string'
        }
    }
    def __init__(self, config=None, core=None):
        super().__init__(config, core)
        self.method = self.config['method']
        self.simulators = self.config['simulators']
        
        

class UtcComparator(Comparator):
    def __init__(self, config=None, core=None):
        super().__init__(config, core)

    def inputs(self): 
        port_schema = {
            f'{simulator}_floating_species': 'tree[string]'
            for simulator in self.simulators 
        }
        port_schema['time'] = 'list[float]'
        return port_schema
    
    def outputs(self):
        return {
            'mean_squared_error': 'tree[string]',
            'proximity': 'tree[string]',
            'output_data': 'tree[string]'  # ie: {spec_id: {sim_name: outputarray}}
        }
        
    def update(self, inputs):
        for simulator in self.simulators:
            species_key = f'{simulator}_floating_species'
            for spec_name, spec_output in inputs[species_key].items():
                print(spec_name)
        
        return {
            'mean_squared_error': {},
            'proximity': {},
            'output_data': {}
        }
                