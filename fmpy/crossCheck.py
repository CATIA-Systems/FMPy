import os
import numpy as np
import matplotlib.pyplot as plt
from collections import Iterable
from fmpy.simulate import simulate

def simulateFMU(path: str, fmu_filename: str, reference_filename: str, input_filename=None, batch_filename=None):

    print(path, fmu_filename)

    ref = np.genfromtxt(os.path.join(path, reference_filename), delimiter=',', names=True)

    if input_filename is not None:
        input = np.genfromtxt(os.path.join(path, input_filename), delimiter=',', names=True)
    else:
        input = None

    time = ref['time']

    sample_interval = time[1] - time[0]
    stop_time = time[-1]

    step_size = stop_time / 1000

    if batch_filename is not None:

        with open(os.path.join(path, batch_filename), 'r') as file:
            for line in file:
                args = line.split(' ')
                if '-h' in args:
                    i = args.index('-h')
                    step_size = float(args[i+1])
                    break

    res = simulate(filename=os.path.join(path, fmu_filename),
                   stop_time=stop_time,
                   step_size=step_size,
                   output=ref.dtype.names[1:],
                   sample_interval=sample_interval,
                   input=input)

    plot_result(res, ref)


def plot_result(result, reference=None):

    import matplotlib.pylab as pylab

    params = {
            # 'legend.fontsize': 'medium',
            #'figure.figsize': (10, 8),
            'legend.fontsize': 'small',
            'axes.labelsize': 'small',
            #   'axes.titlesize': 'medium',
            'xtick.labelsize': 'small',
            'ytick.labelsize': 'small'
    }

    pylab.rcParams.update(params)

    time = result['time']
    names = result.dtype.names[1:]

    if len(names) > 0:

        fig, axes = plt.subplots(len(names), sharex=True)

        fig.set_facecolor('white')

        if not isinstance(axes, Iterable):
            axes = [axes]

        for ax, name in zip(axes, names):

            # ax.grid(True)
            ax.grid(b=True, which='both', color='0.8', linestyle='-', zorder=0)

            if reference is not None and name in reference.dtype.names:
                ax.plot(reference['time'], reference[name], color=(1,0.8,0.8), linewidth=3, label='reference', zorder=100)

            ax.plot(time, result[name], 'b', label='result', zorder=101)

            ax.set_ylabel(name)

            ax.margins(x=0, y=0.1)

        if reference is not None:
            #ax.legend()
            plt.legend(bbox_to_anchor=(0, -0.4, 1., 0.1), loc=8, ncol=2, mode="normal", borderaxespad=0.5)


        fig.set_size_inches(w=12, h=8, forward=True)
        plt.tight_layout()
        fig.subplots_adjust(bottom=0.08)
        plt.show()


if __name__ == '__main__':

    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\FMUSDK\2.0.4'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\CoSimulation\win64\FMIToolbox_MATLAB\2.3'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\Dymola\2017'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\MapleSim\2016.2'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\SimulationX\3.7.41138'
    test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.3.0'

    for subdir, dirs, files in os.walk(test_fmu_dir):

        args = {'path': subdir}

        for file in files:

            if file.endswith('.fmu'):
                args['fmu_filename'] = file

            if file.endswith('_in.csv'):
                args['input_filename'] = file

            if file.endswith('_cc.csv'):
                args['reference_filename'] = file

            if file.endswith('_cc.bat'):
                args['batch_filename'] = file

        if 'fmu_filename' in args:
            simulateFMU(**args)
