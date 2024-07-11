import os 
from abc import ABC, abstractmethod
import numpy as np

from process_bigraph import Composite, Step
from simulariumio.smoldyn import SmoldynConverter, SmoldynData
from simulariumio import (
    UnitData, 
    MetaData, 
    DisplayData, 
    DISPLAY_TYPE, 
    ModelMetaData, 
    BinaryWriter, 
    InputFileData,
)
from simulariumio.filters import TranslateFilte

from biosimulator_processes import CORE 


class SimulariumStep(Step, ABC):
    config_schema = {
        'box_size': 'float',
        'trajectory_title': 'maybe[string]',
        'model_metadata_config': 'maybe[tree[string]]',  # simulariumio.ModelMetaData (optional)
        'time_units': 'maybe[string]',
        'spatial_units': 'maybe[string]'
    }

    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)
    
    @abstractmethod
    def get_display_data(self, data_fp: str):
        # return a simulariumio.DisplayData() with configs extracted from input file
        pass 

    def inputs(self):
        return {
            'species_counts': 'tree[string]',
            'input_file_path': 'string'
        }
    
    def outputs(self):
        return {
            'simularium_file_path': 'string'
        }


class SimulariumSmoldyn(SimulariumStep):
    def __init__(self, config=None, core=CORE):
        super().__init__(config, core)

    def get_display_data(self, data_fp: str):
        pass 

    def update(self, inputs, interval):
        input_fp = inputs['input_file_path']
        species_counts = inputs['species_counts']
        species_names = list(species_counts.keys())

        display_data = self.get_display_data(input_fp)
        simularium_data = SmoldynData(
            smoldyn_file=input_fp
        )




    