"""class IntervalResult(BaseModel):
    global_time_stamp: float
    results: Dict[str, Any]


class SimulatorResult(BaseModel):
    process_id: str
    simulator: str
    result: List[IntervalResult]


class ComparisonResults(BaseModel):
    duration: int
    num_steps: int
    values: List[SimulatorResult]

{('emitter',): [{
    'copasi': [
        {
            'floating_species_concentrations': {
                'plasminogen': 0.0,
                'plasmin': 0.0,
                'single intact chain urokinase-type plasminogen activator': 0.0,
                'two-chain urokinase-type plasminogen activator': 0.0,
                'x': 0.0,
                'x-plasmin': 0.0},
           'time': 0.0
        },
        ...
    ],
    'amici': [
        {
            'floating_species_concentrations': {
                'plasminogen': 1.1758171177387002e+16,
                'plasmin': 1096150505274.1506,
                'single intact chain urokinase-type plasminogen activator': 2955755808974603.0,
                'two-chain urokinase-type plasminogen activator': 80249.33829510311,
                'x': 0.0,
                'x-plasmin': 0.0},
           'time': 0.0},
        },
       ...
    ]


"""

from typing import Dict, List

from process_bigraph import Composite

from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import IntervalOutputData, SimulatorProcessOutput, ODEComparisonResult, ProcessComparisonResult


async def generate_ode_process_comparison(biomodel_id: str, duration: int, num_steps: int) -> ODEComparisonResult:
    return ODEComparisonResult(duration=duration, biomodel_id=biomodel_id, num_steps=num_steps)


def generate_ode_comparison(biomodel_id: str, dur: int) -> Dict:
    """Run the `compare_ode_step` composite and return data which encapsulates another composite
        workflow specified by dir.

        Args:
            biomodel_id:`str`: A Valid Biomodel ID.
            dur:`int`: duration of the internal composite simulation.

        Returns:
            `Dict` of simulation comparison results like `{'outputs': {...etc}}`
    """
    compare = {
        'compare_ode': {
            '_type': 'step',
            'address': 'local:compare_ode_step',
            'config': {'biomodel_id': biomodel_id, 'duration': dur},
            'inputs': {},
            'outputs': {'comparison_data': ['comparison_store']}
        },
        'verification_data': {
            '_type': 'step',
            'address': 'local:ram-emitter',
            'config': {
                'emit': {'comparison_data': 'tree[any]'}
            },
            'inputs': {'comparison_data': ['comparison_store']}
        }
    }

    wf = Composite(config={'state': compare}, core=CORE)
    wf.run(1)
    comparison_results = wf.gather_results()
    output = comparison_results[("verification_data"),][0]['comparison_data']

    return {'outputs': output[('emitter',)]}


def generate_ode_comparison_result_object(
        results: Dict,
        duration: int,
        n_steps: int,
        simulators: List[str],
        timestamp: str) -> ODEComparisonResult:
    """Factory for `ODEComparisonResult`.

        Args:
            results:`Dict`: results of `generate_ode_comparison()`.
            duration:`int`: duration of the internal composite simulation.
            n_steps:`int`: number of steps of internal composite simulation.
            simulators:`List[str]`: simulator names used in comparison.
            timestamp:`str`: timestamp of simulation run...use date and time

        Returns:
            `ODEComparisonResult`: object representing comparison result.
                Please note: this object is polymorphic with pydantic `BaseClass`, and thus can
                be easily serialized with the `.model_dump()` method.
    """
    process_outputs = []
    for interval_output in results['outputs']:
        for process_output_name, process_output_val in interval_output.items():
            simulator_process_id = process_output_name.split("_f")[0]
            simulator_id = simulator_process_id.split("_")[0]

            process_output_data = []
            if isinstance(process_output_val, dict):
                for output_name, output_val in process_output_val.items():
                    output_
                    output_data = OutputData(
                        name=output_name,
                        value=output_val,
                        time_id=output['time'])
                    process_output_data.append(output_data)

            process_output = SimulatorProcessOutput(
                process_id=simulator_process_id,
                simulator=simulator_id,
                data=process_output_data)
            process_outputs.append(process_output)

    return ODEComparisonResult(
        duration=duration,
        num_steps=n_steps,
        simulators=simulators,
        outputs=process_outputs,
        timestamp=timestamp)


def process_comparison(biomodel_id: str, simulators: List[str], duration: int, n_steps: int, timestamp: str) -> ProcessComparisonResult:
    # TODO: Implement this.
    pass


def ode_comparison(biomodel_id: str, duration: int, n_steps: int, timestamp: str) -> ODEComparisonResult:
    simulators = ['copasi', 'tellurium', 'amici']
    results_dict = generate_ode_comparison(biomodel_id, duration)
    return generate_ode_comparison_result_object(results_dict, duration, n_steps, simulators, timestamp)
