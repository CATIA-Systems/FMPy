from fmpy import simulate_fmu, platform
import requests
import numpy as np


def simulate_coupled_clutches(fmi_version='2.0',
                              fmi_type='CoSimulation',
                              output=['outputs[1]', 'outputs[2]', 'outputs[3]', 'outputs[4]'],
                              fmi_logging=False,
                              show_plot=True):

    # download the FMU and input file
    for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
        url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_' + fmi_version + '/'
        url += fmi_type + '/'
        url += platform + '/MapleSim/2016.2/CoupledClutches/' + filename
        print('Downloading ' + url)

        status_code = -1

        # try to download the file three times
        try:
            for _ in range(3):
                if status_code != 200:
                    response = requests.get(url)
                    status_code = response.status_code
        except:
            pass

        if status_code != 200:
            print("Download failed")
            return None

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
        'start_values': {'CoupledClutches1_freqHz': 0.4},
        'input': input,
        'output': output,
        'validate': False,
        'fmi_logging': fmi_logging
    }

    print("Simulating CoupledClutches.fmu (FMI %s, %s)..." % (fmi_version, fmi_type))
    result = simulate_fmu(**args)

    if show_plot:

        print("Plotting results...")

        import matplotlib.pyplot as plt

        time = result['time']
        names = result.dtype.names[1:]

        fig, axes = plt.subplots(len(names), sharex=True)

        if len(names) == 1:
            axes = [axes]

        for ax, name in zip(axes, names):
            ax.plot(time, result[name])
            ax.set_ylabel(name)
            ax.grid(True)
            ax.margins(x=0, y=0.1)

        plt.tight_layout()
        plt.show()

    print("Done.")

    return result

if __name__ == '__main__':

    simulate_coupled_clutches()
