import tempfile
import os 
from datetime import datetime
import json
from process_bigraph import Composite
from biosimulator_processes import CORE


class ProcessUnitTest:
    def __init__(self, instance_doc: dict, duration=10, write_results=False, out_dir=None):
        self.instance_doc = instance_doc
        self.duration = duration
        self._run(write_results, out_dir)

    def create_composite(self) -> Composite:
        return Composite(
            config={'state': self.instance_doc},
            core=CORE)

    def __run_workflow(self, composite: Composite) -> None:
        return composite.run(self.duration)

    def get_results(self, composite: Composite) -> dict:
        self.__run_workflow(composite)
        return composite.gather_results()

    def write_results(self, results: dict, out_dir: str = None):
        results_dest = str(datetime.now()).replace(' ', '__').replace(':', '_')
        if out_dir is None:
            out_dir = tempfile.mkdtemp()

        save_fp = os.path.join(out_dir, results_dest) + '.json'
        with open(save_fp, 'w') as fp:
            return json.dump(results, fp, indent=4)

    def _run(self, write_results=False, out_dir: str = None):
        composite = self.create_composite()
        results = self.get_results(composite)
        if write_results:
            return self.write_results(results, out_dir)
        else:
            print(f'THE TEST RESULTS:\n{results}')
