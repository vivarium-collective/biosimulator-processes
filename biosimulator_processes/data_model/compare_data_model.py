from typing import *


__all__ = ['ComparisonDocument']


class ComparisonDocument:
    """To be called 'behind-the-scenes' by the Comparison REST API"""
    def __init__(self,
                 simulators: List[str],
                 duration: int,
                 num_steps: int,
                 model_filepath: str,
                 framework_type='deterministic',
                 target_parameter: Dict[str, Union[str, float]] = None):
        self.simulators = simulators
        self.composite = {}
        self.framework_type = framework_type
        context = 'concentrations' if 'deterministic' in self.framework_type else 'counts'
        self.species_port_name = f'floating_species_{context}'
        self.species_store = [f'floating_species_{context}_store']
        self._populate_composition(model_filepath)
        self._add_emitter()

    def _generate_composite_index(self) -> float:
        # TODO: implement this.
        pass

    def _add_emitter(self):  # TODO: How do we reference different nesting levels?
        self.composite['emitter'] = {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {
                    self.species_port_name: 'tree[float]',
                    'time': 'float'}
            },
            'inputs': {
                self.species_port_name: self.species_store,
                'time': ['time_store']}
        }

    def _populate_composition(self, model_filepath: str):
        context = 'concentrations' if 'deterministic' in self.framework_type else 'counts'
        for index, process in enumerate(self.simulators):
            self._add_ode_process_schema(
                process_name=process,
                species_context=context,
                i=index,
                model={'model_source': model_filepath}
            )

    def _add_ode_process_schema(
            self,
            process_name: str,
            species_context: str,
            i: int,
            **config
    ) -> None:
        species_port_name = f'floating_species_{species_context}'
        species_store = [f'floating_species_{species_context}_store']
        self.composite[f'{process_name}_{i}'] = {
            '_type': 'process',
            'address': f'local:{process_name}',
            'config': config,
            'inputs': {
                species_port_name: species_store,
                'model_parameters': ['model_parameters_store'],
                'time': ['time_store'],
                'reactions': ['reactions_store']
            },
            'outputs': {
                species_port_name: species_store,
                'time': ['time_store']
            }
        }
