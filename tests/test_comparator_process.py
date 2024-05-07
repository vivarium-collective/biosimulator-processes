import os
import json

from process_bigraph import Composite, pp
from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import ODEComparisonDocument


def test_ode_comparison_process():
    biomodel_id = 'BIOMD0000000630'
    model_fp = f'biosimulator_processes/model_files/sbml/BIOMD0000000630_url.xml'
    duration = 30

    comparison_instance = ODEComparisonDocument(
        simulators={''}
    )
