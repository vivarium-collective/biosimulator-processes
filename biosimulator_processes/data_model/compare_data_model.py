"""
Compare Data Model:
    Objects whose purpose is to compare the output of 'like-minded' simulators/processes
which reside in a shared compositional space. The global 'state' of this composition
is agnostic to any summation of values.

author: Alex Patrie
license: Apache License, Version 2.0
date: 04/2024
"""

from typing import *
from abc import ABC
from dataclasses import dataclass

from pydantic import Field, field_validator

from biosimulator_processes.utils import prepare_single_ode_process_document
from biosimulator_processes.data_model import _BaseModel as BaseModel


"""
Such engineering should be performed by an expeditionary of semantic unity, using 
vocabulary as their protection. The Explorer is truly that: unafraid to step outside of
the unifying 'glossary' in the name of expanding it. Semantics are of both great
use and immense terror to the Explorer. The Explorer firmly understands and believes 
these worldly facts. 


For example: 

result = ComparisonResults(
            10, 
            20, 
            'BIOMD0000023', 
            [
                SimulatorResult(
                    my_process, 
                    copasi, 
                    [
                        IntervalResult(
                            0, 
                            [
                                ResultData('T', 2.9, 0.7)
                            ]
                    ]
                )
            ]

"""


class ResultData(BaseModel):
    name: str
    value: float
    target: float
    mse: float = Field(...)

    def __init__(self, name: str, value: float, target: float):
        self.name = name
        self.value = value
        self.target = target
        self.mse = self._set_mse()

    def _set_mse(self):
        return (self.target - self.value) ** 2


class IntervalResult(BaseModel):
    interval_id: float  # should be Composite.state['global_time']
    data: List[ResultData]


class MSEValues(BaseModel):
    param_name: str
    value: float


class RMSE(BaseModel):
    process_id: str
    param_id: str  # mostly species names or something like that
    value: Union[float, int]
    _mse_values: List[MSEValues]  # set internally


# Based on the list of interval results
class ODEProcessFitnessScore(BaseModel):
    process_id: str
    rmse_values: List[RMSE]


class SimulatorProcessResult(BaseModel):
    simulator: str
    process_id: str
    data: List[IntervalResult]
    fitness_score: ODEProcessFitnessScore


class SimulatorComparisonResult(BaseModel):
    duration: int
    num_steps: int
    simulators: List[str]
    outputs: Union[List[SimulatorProcessResult], Dict]


class ProcessAttributes(BaseModel):
    name: str
    initial_state: Dict[str, Any]
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]


class CompositeRunError(BaseModel):
    exception: Exception


class ComparisonDocument(ABC):
    def __init__(self):
        pass


class ODEComparisonDocument(ComparisonDocument):
    """To be called 'behind-the-scenes' by the Comparison REST API"""
    def __init__(self,
                 duration: int,
                 num_steps: int,
                 model_filepath: str,
                 framework_type='deterministic',
                 simulators: Optional[Union[List[str], Dict[str, str]]] = None,
                 target_parameter: Optional[Dict[str, Union[str, float]]] = None,
                 **kwargs):
        """This object implements a self generated factory with which it creates its representation. The naming of
            simulator processes within the composition are by default generated through concatenating the simulator
            tool _name_(i.e: `'tellurium'`) with with a simple index `i` which is a population of an iteration over
            the total number of processes in the bigraph.

                Args:
                    simulators:`Union[List[str], Dict[str, str]]`: either a list of actual simulator tool names,
                        ie: `'copasi'`; or a dict mapping of {simulator_tool_name: custom_process_id}
                    duration:`int`: the total duration of simulation run
                    num_steps:`int`
                    model_filepath:`str`: filepath which points to a SBML model file.
                    framework_type:`str`: type of mathematical framework to employ with the simulators within your
                        composition. Choices are `'stochastic'`, `'deterministic'`. Note that there may be more
                        stochastic options than deterministic.
        """
        super().__init__()

        if simulators is None:
            self.simulators = ['tellurium', 'copasi', 'amici']
        elif isinstance(simulators, dict):
            self.simulators = list(simulators.keys()) if isinstance(simulators, dict) else simulators
            self.custom_process_ids = list(simulators.values())
        else:
            self.simulators = simulators

        self.composite = kwargs.get('composite', {})
        self.framework_type = framework_type

        context = 'concentrations'
        self.species_port_name = f'floating_species_{context}'
        self.species_store = [f'floating_species_{context}_store']
        self._populate_composition(model_filepath)

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

    def _add_emitter(self) -> None:  # TODO: How do we reference different nesting levels?
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
                'time': ['time_store']}}

    def _populate_composition(self, model_filepath: str):
        context = 'concentrations'
        for index, process in enumerate(self.simulators):
            self._add_ode_process_schema(
                process_name=process,
                species_context=context,
                i=index,
                model={'model_source': model_filepath})
        return self._add_emitter()

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
