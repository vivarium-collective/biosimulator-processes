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

from typing import Dict

from process_bigraph import Composite

from biosimulator_processes import CORE
from biosimulator_processes.data_model.compare_data_model import OutputData, SimulatorProcessOutput, ODEComparisonResult


def generate_ode_comparison(biomodel_id, dur) -> Dict:
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
    # print(f'comparison results:\n{comparison_results[("verification_data",)]}')
    output = comparison_results[("verification_data"),][0]['comparison_data']
    return {'outputs': output[('emitter',)]}


def generate_ode_comparison_result_object(results, duration, n_steps, simulators) -> ODEComparisonResult:
    process_outputs = []
    for interval_output in results['outputs']:
        outputs = []
        for name, val in interval_output.items():
            if isinstance(val, dict):
                for output_name, output_val in val.items():
                    output_data = OutputData(name=output_name, value=output_val)
                    outputs.append(output_data)
            elif isinstance(val, float):
                output_data = OutputData(name=name, value=val)
                outputs.append(output_data)
        process_id = list(interval_output.keys())[0]
        process_simulator = process_id.split('_')[0]
        process_output = SimulatorProcessOutput(process_id=process_id, simulator=process_simulator, data=outputs)
        process_outputs.append(process_output)

    return ODEComparisonResult(duration=duration, num_steps=n_steps, simulators=simulators, outputs=process_outputs)

