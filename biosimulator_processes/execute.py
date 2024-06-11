import os

from biosimulator_processes.processes.amici_process import UtcAmici
from biosimulator_processes.processes.copasi_process import UtcCopasi
from biosimulator_processes.processes.tellurium_process import UtcTellurium
from biosimulator_processes.steps.comparator_step import UtcComparator


def exec_utc_comparison(omex_fp: str, simulators: list[str], comparison_id: str = None, include_outputs: bool = True):
    utc_tellurium = UtcTellurium(config={'model': {'model_source': omex_fp}})
    tellurium_results = utc_tellurium.update()

    utc_copasi = UtcCopasi(config={'model': {'model_source': omex_fp}})
    copasi_results = utc_copasi.update()

    utc_amici = UtcAmici(config={'model': {'model_source': omex_fp}})
    amici_results = utc_amici.update()

    comparison_input_state = {
        'amici_floating_species': amici_results['floating_species'],
        'copasi_floating_species': copasi_results['floating_species'],
        'tellurium_floating_species': tellurium_results['floating_species']
    }
    comparator = UtcComparator(
        config={
            'simulators': simulators,
            'comparison_id': comparison_id or 'utc-comparison',
            'include_output_data': include_outputs
        }
    )
    return comparator.update(comparison_input_state)


def sbml_utc_comparison_scan(sbml_source_dir: str, simulators: list[str]):
    archive_filepaths = [
        os.path.join(sbml_source_dir, f)
        for f in os.listdir(sbml_source_dir) if not os.path.isdir(f)
    ]

    scan_results = {}
    for fp in archive_filepaths:
        # comparison_doc = UtcComparisonDocument(model_source=fp)
        f_key = fp.split('/')[-1]
        try:
            scan_results[f_key] = exec_utc_comparison(fp, simulators)
        except:
            scan_results[f_key] = {'error': f'At least one simulator did not support {f_key}'}
    return scan_results
