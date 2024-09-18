"""
Simulator functions derived from the update methods of Utc processes and more.
"""

# TODO: Copy the utc functions from bio-check/compose_worker/output_data.py !!!


def run_amici():
    pass


def run_copasi():
    pass


def run_tellurium():
    pass


SIMULATOR_FUNCTIONS = dict(zip(
    ['amici', 'copasi', 'tellurium'],
    [run_amici, run_copasi, run_tellurium]
))


