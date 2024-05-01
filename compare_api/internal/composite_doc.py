from typing import *
from process_bigraph import Composite
from biosimulator_processes import CORE
from biosimulator_processes.compare import ComparisonDocument


def create_comparison_document(
        sbml_model_path: str,
        simulators: list[str],
        duration: int,
        n_steps: int,
        target_param: dict = None
        ) -> ComparisonDocument:
    return ComparisonDocument(
        simulators=simulators,
        duration=duration,
        num_steps=n_steps,
        model_filepath=sbml_model_path,
        target_parameter=target_param)


def generate_workflow(document: ComparisonDocument) -> Composite:
    return Composite(
        config={'state': document.composite},
        core=CORE)


async def run_workflow(workflow: Composite, duration: int) -> Dict:
    workflow.run(duration)
    return workflow.gather_results()
