"""Comparator Step:

    Here the entrypoint is the results of an emitter.
"""


from tempfile import mkdtemp

from process_bigraph import Step, pp, Composite

from biosimulator_processes import CORE
from biosimulator_processes.io import fetch_sbml_file


class ODEComparatorStep(Step):
    config_schema = {'biomodel_id': 'string', 'duration': 'integer'}

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
        self.biomodel_id = self.config['biomodel_id']
        self.duration = self.config['duration']

    def inputs(self):
        return {}

    def outputs(self):
        return {'comparison': 'tree[any]'}

    def update(self, state):
        results = self._run_workflow()
        return {'comparison_data': results}

    def _run_workflow(self):
        directory = mkdtemp()
        model_fp = fetch_sbml_file(self.biomodel_id, save_dir=directory)

        manuscript = {
            'copasi_simple': {
                '_type': 'process',
                  'address': 'local:copasi',
                  'config': {'model': {'model_source': model_fp}},
                  'inputs': {'floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                   'model_parameters': ['model_parameters_store'],
                   'time': ['time_store'],
                   'reactions': ['reactions_store']},
                  'outputs': {'floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                   'time': ['time_store']}
            },
            'amici_simple': {
                '_type': 'process',
                'address': 'local:amici',
                'config': {'model': {'model_source': model_fp}},
                'inputs': {
                    'floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                    'model_parameters': ['model_parameters_store'],
                    'time': ['time_store'],
                    'reactions': ['reactions_store']},
                'outputs': {
                    'floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                    'time': ['time_store']}
            },
            'emitter': {
                 '_type': 'step',
                  'address': 'local:ram-emitter',
                  'config': {
                      'emit': {
                          'copasi_simple_floating_species_concentrations': 'tree[float]',
                          'amici_simple_floating_species_concentrations': 'tree[float]',
                          'tellurium_simple_floating_species_concentrations': 'tree[float]',
                          'time': 'float'
                      }
                  },
                  'inputs': {
                      'copasi_simple_floating_species_concentrations': ['copasi_simple_floating_species_concentrations_store'],
                      'amici_simple_floating_species_concentrations': ['amici_simple_floating_species_concentrations_store'],
                      'tellurium_simple_floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                      'time': ['time_store']
                  }
            },
            'tellurium_simple': {
                '_type': 'process',
                  'address': 'local:tellurium',
                  'config': {'model': {'model_source': model_fp}},
                  'inputs': {'floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                   'model_parameters': ['model_parameters_store'],
                   'time': ['time_store'],
                   'reactions': ['reactions_store']},
                  'outputs': {'floating_species_concentrations': ['tellurium_simple_floating_species_concentrations_store'],
                   'time': ['time_store']}}}

        comp = Composite(config={'state': manuscript}, core=CORE)
        comp.run(self.duration)
        return comp.gather_results()[('emitter',)]
