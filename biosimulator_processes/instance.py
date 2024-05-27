import matplotlib.pyplot as plt
from process_bigraph.experiments.parameter_scan import RunProcess

from biosimulator_processes import CORE
from biosimulator_processes.steps.ode_simulation import ODEProcess


def get_observables(proc: RunProcess):
    observables = []
    for port_name, port_dict in proc.process.inputs().items():
        if port_name.lower() == 'floating_species_concentrations':
            if isinstance(port_dict, dict):
                for name, typeVal in port_dict.items():
                    obs = [port_name, name]
                    observables.append(obs)
            else:
                obs = [port_name]
                observables.append(obs)
    return observables


def generate_ode_instance(process_address: str, model_fp: str, step_size: float, duration: float) -> ODEProcess:
    ode_process_config = {'model': {'model_source': model_fp}}
    proc = RunProcess(
        config={
            'process_address': process_address,
            'process_config': ode_process_config,
            'timestep': step_size,
            'runtime': duration},
        core=CORE)
    obs = get_observables(proc)

    return ODEProcess(
        address=process_address,
        model_fp=model_fp,
        observables=obs,
        step_size=step_size,
        duration=duration)


def plot_ode_output_data(data: dict):
    time = data.get('results', data['time'])
    spec_outputs = []
    for name, output in data['floating_species'].items():
        spec_outputs.append({name: output})

    # Plotting the data
    plt.figure(figsize=(8, 6))
    for output in spec_outputs:
        for name, out in output.items():
            plt.plot(time, out, label=name)

    plt.xlabel('Time')
    plt.ylabel('Concentration')
    plt.title('Species Concentrations Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

