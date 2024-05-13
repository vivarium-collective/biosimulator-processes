from typing import *
from process_bigraph import Composite
from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import ODEComparisonDocument


def create_comparison_document(
        sbml_model_path: str,
        simulators: list[str],
        duration: int,
        n_steps: int,
        target_param: dict = None
        ) -> ODEComparisonDocument:
    return ODEComparisonDocument(
        simulators=simulators,
        duration=duration,
        num_steps=n_steps,
        model_filepath=sbml_model_path,
        target_parameter=target_param)


def generate_workflow(document: ODEComparisonDocument) -> Composite:
    return Composite(
        config={'state': document.composite},
        core=CORE)


async def run_workflow(workflow: Composite, duration: int) -> Dict:
    workflow.run(duration)
    return workflow.gather_results()


"""Timescale, num_steps, sbml model path, sbml model file upload, omex, sbml string. Metadata."""
