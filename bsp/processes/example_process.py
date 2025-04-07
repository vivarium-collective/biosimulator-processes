from process_bigraph import Process


class Tx(Process):
    config_schema = {
        'ktsc': 'float',
        'kdeg': 'float',
        'k': 'float'
    }

    def __init__(self, config=None, core=None):
        super().__init__(config=config, core=core)
        
        self.ktsc = self.config.get('ktsc', 1e-2)
        self.kdeg = self.config.get('kdeg', 1e-3)
        self.k = self.config.get('k', 1e-11)
    
    def initial_state(self):
        return {
            'DNA': 10,
            'mRNA': 100.0,
            'dC': 0
        }
    
    def inputs(self):
        return {
            'DNA': 'float',
            'mRNA': 'float'
        }
    
    def outputs(self):
        return {
            'DNA': 'float',
            'mRNA': 'float',
            'dC': 'float'
        }

    def update(self, state, interval):
        G = state['DNA'] + self.k
        C = state['mRNA'] + self.k
        dC = (self.ktsc * G - self.kdeg * C) * interval
        return {
            'DNA': G,
            'mRNA': C,
            'dC': dC
        }
