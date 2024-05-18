from process_bigraph import pf, pp

from test_suite.test_processes.test_process import test_ode_sed_processes


# TODO: adopt these for CLI with cement?
def test_main_ode(model_entrypoint: str, n_steps: int, dur: int):
    """
        1. structural assumptions -> test model file entrypoint and process update (1) manually. Assert expected outputs
            from processes (as seen in examples omex dirs).

        2. data assumptions -> test model config entrypoint with custom params like species, params, reactions, etc. HERE is
            where the comparison matrices should be analyzed. Also, implement "stress test".

        3. is it publishable? -> is the omex properly formatted with process output?
            TODO: make utility for auto gen expected output from process config.
    """
    composition_results = test_ode_sed_processes(model_entrypoint=model_entrypoint, num_steps=n_steps, duration=dur)
    pp(composition_results)

