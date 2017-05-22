import fmpy
import requests
import os
import numpy as np
import matplotlib.pyplot as plt


def simulate_coupled_clutches(show_plot=True):

    # download the FMU and input file
    for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
        if not os.path.isfile(filename):
            url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/' + fmpy.platform + '/MapleSim/2016.2/CoupledClutches/' + filename
            print('Downloading ' + filename)
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
        'step_size': 1e-3,
        'sample_interval': 2e-3,
        'fmi_type': fmpy.CO_SIMULATION,
        'start_values': {},
        'input': input,
        'output': ['inputs', 'outputs[1]', 'outputs[2]', 'outputs[3]', 'outputs[4]'],
    }

    print("Simulating...")
    result = fmpy.simulate_fmu(**args)

    if show_plot:

        print("Plotting results...")

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
