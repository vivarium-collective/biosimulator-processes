from dataclasses import dataclass

from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE


@dataclass
class OutputAspectVerification:
    aspect_type: str  # one of: 'names', 'values'. TODO: Add more
    is_verified: bool
    expected_data: any
    process_data: any


class ODEProcess(RunProcess):
    def __init__(self, config=None, core=CORE, **kwargs):
        """ODE-based wrapper of RunProcess from process_bigraph.

            kwargs:
                'process_address': 'string',
                'process_config': 'tree[any]',
                'observables': 'list[path]',
                'timestep': 'float',
                'runtime': 'float'
        """
        configuration = config or kwargs
        configuration['observables'] = kwargs.get('observables') or self.set_observables()
        super().__init__(configuration, core)

    def set_observables(self):
        return [(k, v) for k, v in self.process.inputs().items()]
