from fmpy import CO_SIMULATION, MODEL_EXCHANGE, simulate_fmu, platform
import requests
import os
import numpy as np


def simulate_coupled_clutches(fmi_version='2.0', fmi_type=CO_SIMULATION, show_plot=True):

    # download the FMU and input file
    for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
        url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_' + fmi_version + '/'
        url += ('CoSimulation' if fmi_type == CO_SIMULATION else 'ModelExchange') + '/'
        url += platform + '/MapleSim/2016.2/CoupledClutches/' + filename
        print('Downloading ' + url)
        response = requests.get(url)
        with open(filename, 'wb') as f:
            f.write(response.content)

    print("Loading input...")
    input = np.genfromtxt('CoupledClutches_in.csv', delimiter=',', names=True)

    # set the parameters for the simulation
    args = {
        'filename': 'CoupledClutches.fmu',
        'start_time': 0,
        'stop_time': 1.5,
        'step_size': 1e-2,
        'sample_interval': 2e-2,
        'fmi_type': fmi_type,
        'start_values': {},
        'input': input,
        'output': ['inputs', 'outputs[1]', 'outputs[2]', 'outputs[3]', 'outputs[4]'],
        'validate': False
    }

    print("Simulating CoupledClutches.fmu (FMI %s, %s)..." % (fmi_version, 'Co-Simulation' if fmi_type == CO_SIMULATION else 'Model Exchange'))
    result = simulate_fmu(**args)

    if show_plot:

        print("Plotting results...")

        import matplotlib.pyplot as plt

        time = result['time']
        names = result.dtype.names[1:]

        fig, axes = plt.subplots(len(names), sharex=True)

        for ax, name in zip(axes, names):
            ax.plot(time, result[name])
            ax.set_ylabel(name)
            ax.grid(True)
            ax.margins(x=0, y=0.1)

        plt.tight_layout()
        plt.show()

    print("Done.")


if __name__ == '__main__':

    simulate_coupled_clutches()
