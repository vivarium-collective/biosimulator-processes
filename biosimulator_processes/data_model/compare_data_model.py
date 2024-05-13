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

import numpy as np
from pydantic import Field, field_validator

from biosimulator_processes.utils import prepare_single_ode_process_document
from biosimulator_processes.steps.comparator_step import calculate_mse
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


class ParameterScore(BaseModel):
    """Base class for parameter scores in-general."""
    param_name: str
    value: float


class ParameterMSE(ParameterScore):
    """Attribute of Process Parameter RMSE"""
    param_name: str
    value: float = Field(...)  # TODO: Ensure field validation/setting for MSE-specific calculation.
    mean: float
    process_id: str

    @classmethod
    @field_validator('value')
    def set_value(cls, v):
        # TODO: Finish this.
        return v


class ProcessParameterRMSE(BaseModel):
    """Attribute of Process Fitness Score"""
    process_id: str
    param_id: str  # mostly species names or something like that

    def __init__(self, process_id, param_id, mse_values: List[float]):
        self.process_id = process_id
        self.param_id = param_id
        self.value = self._set_value(mse_values)

    def _set_value(self, values: List[float]):
        """Calculate the RMSE for a given parameter and trajectory values"""
        all_mse_values = []

        for time_point_data in values:
            mse_values = calculate_mse(time_point_data)
            all_mse_values.extend(mse_values)

        # Calculate the mean of all MSE values
        mean_mse = np.mean(all_mse_values)

        # Calculate RMSE
        rmse = np.sqrt(mean_mse)

        return rmse



class ProcessFitnessScore(BaseModel):
    """Attribute of Simulator Process Output Based on the list of interval results"""
    process_id: str
    error: float  # the error by which to bias the rmse calculation
    rmse_values: List[ProcessParameterRMSE]  # indexed by parameter name over whole simulation


class IntervalOutputData(BaseModel):
    """Attribute of Simulator Process Output"""
    param_name: str  # data name
    value: float
    time_id: float  # index for composite run inference
    mse: ParameterMSE


class SimulatorProcessOutput(BaseModel):
    """Attribute of Process Comparison Result"""
    process_id: str
    simulator: str
    data: List[IntervalOutputData]
    fitness_score: ProcessFitnessScore


class ProcessComparisonResult(BaseModel):
    """Generic class inherited for all process comparisons."""
    duration: int
    num_steps: int
    simulators: List[str]
    outputs: List[SimulatorProcessOutput]
    timestamp: str


class ODEComparisonResult(ProcessComparisonResult):
    duration: int
    num_steps: int
    simulators: List[str] = ['tellurium', 'copasi', 'amici']
    outputs: List[SimulatorProcessOutput]
    timestamp: str


class ProcessAttributes(BaseModel):
    name: str
    initial_state: Dict[str, Any]
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


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
