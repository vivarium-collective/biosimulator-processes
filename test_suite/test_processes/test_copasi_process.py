import os
import json

from process_bigraph import Composite, pp
from biosimulator_processes import CORE
from biosimulator_processes.helpers import prepare_single_ode_process_document


def test_process():
    biomodel_id = 'BIOMD0000000630'
    model_fp = f'biosimulator_processes/model_files/sbml/BIOMD0000000630_url.xml'
    species_context = 'counts'
    species_port_name = f'floating_species_{species_context}'
    species_store = [f'floating_species_{species_context}_store']
    duration = 10

    print(os.path.exists(model_fp))

    instance = prepare_single_ode_process_document(
        simulator_name='copasi',
        process_id=f'{biomodel_id}_copasi_process',
        sbml_model_fp=model_fp)

    composition = Composite(config={'state': instance}, core=CORE)
    composition.run(duration)
    results = composition.gather_results()
    return pp(results)


# def test_process_from_document():
#     # read the document from local file:
#     five_process_fp = 'composer-notebooks/out/five_process_composite.json'
#     with open(five_process_fp, 'r') as fp:
#         instance = json.load(fp)
#
#     return ProcessUnitTest(instance, duration=10)


if __name__ == '__main__':
    test_process()
