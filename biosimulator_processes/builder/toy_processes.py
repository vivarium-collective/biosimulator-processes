from biosimulator_processes.process_bigraph import Process, Composite, process_registry, types


class IncreaseProcess(Process):
    config_schema = {
        'rate': {
            '_type': 'float',
            '_default': '0.1'}}

    def __init__(self, config=None):
        super().__init__(config)

    def inputs(self):
        return {
            'level': 'float'}

    def outputs(self):
        return {
            'level': 'float'}

    def update(self, state, interval):
        return {
            'level': state['level'] * self.config['rate']}


# register the processes
process_registry.register('increase', IncreaseProcess)
