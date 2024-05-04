from typing import *
from abc import ABC
from dataclasses import dataclass
from biosimulator_processes.utils import prepare_single_ode_process_document


__all__ = ['ComparisonDocument']


class ComparisonDocument(ABC):
    def __init__(self):
        pass


class ODEComparisonDocument(ComparisonDocument):
    """To be called 'behind-the-scenes' by the Comparison REST API"""
    def __init__(self,
                 simulators: List[str],
                 duration: int,
                 num_steps: int,
                 model_filepath: str,
                 framework_type='deterministic',
                 target_parameter: Dict[str, Union[str, float]] = None,
                 **kwargs):
        super().__init__()
        self.simulators = simulators
        self.composite = kwargs.get('composite') or {}
        self.model_filepath = model_filepath
        self.framework_type = framework_type
        context = 'concentrations' if 'deterministic' in self.framework_type else 'counts'
        self.species_port_name = f'floating_species_{context}'
        self.species_store = [f'floating_species_{context}_store']
        self._populate_composition(model_filepath)
        self._add_emitter()

    def add_single_process_to_composite(self, process_id: str, simulator: str):
        process_instance = prepare_single_ode_process_document(
            process_id=process_id,
            simulator_name=simulator,
            sbml_model_fp=self.model_filepath,
            add_emitter=False)
        self.composite[process_id] = process_instance[process_id]

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


class DocumentFactory:
    @classmethod
    def from_dict(cls, configuration: Dict) -> ComparisonDocument:
        """
            Args:
                configuration:`Dict`: required keys:
                     simulators: List[str],
                     duration: int,
                     num_steps: int,
                     model_filepath: str,
                     framework_type='deterministic',
                     target_parameter: Dict[str, Union[str, float]] = None

        """
        return ComparisonDocument(**configuration)
