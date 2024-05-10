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


from process_bigraph import Composite

from biosimulator_processes import CORE


def generate_ode_comparison(biomodel_id, dur) -> dict:
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
    
    return comparison_results

