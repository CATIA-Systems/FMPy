""" This example shows a full factorial variation of two model parameters
using multiple cores.

The goal of this experiment is to determine the losses of a Rectifier for
different AC voltages and DC currents. Therefore the Rectifier.fmu is simulated
for every parameter combination. The losses after 0.02 s (when a steady state has
been reached) are averaged and returned as the result and plotted as a contour plot.
"""

import dask
from dask import bag
from dask.diagnostics import ProgressBar
import numpy as np
import fmpy
from fmpy.fmi2 import FMU2Slave
from fmpy import read_model_description, platform
from fmpy.util import download_test_file
import shutil


fmu_filename = 'Rectifier.fmu'

# define the parameter space for the variation
v_ac = [100, 150, 200, 250, 300, 350, 400, 450, 500]  # AC voltage [V]
i_dc = [20, 30, 40, 50, 60, 70, 80, 90, 100]          # DC current [A]

sync = False  # synchronized execution (for debugging)

stop_time = 0.1

dll_handle = None

n_chunks = 10  # number of chunks to divide the workload

# create the parameters
V_AC, I_DC = np.meshgrid(v_ac, i_dc, indexing='ij')


def simulate_fmu(*args):
    """ Worker function that simulates the FMU

    Parameters:
        args = [indices, fmu_args, start_vrs, result_vrs]

        indices     a list of indices into the parameter arrays
        fmu_args    FMU constructor arguments


    Returns:
        a list of tuples (i, [u_dc, losses]) that contain the index 'i' and the averaged results of the
        'uDC' and 'Losses' variables
    """

    indices, fmu_args, start_vrs, result_vrs = args

    zipped = []

    # global fmu_args, start_vrs, result_vrs, dll_handle

    fmu = FMU2Slave(**fmu_args)

    fmu.instantiate()

    # iterate over the all indices in this batch
    for i in indices:

        # get the start values for the current index
        start_values = [V_AC[i], I_DC[i]]

        fmu.reset()

        fmu.setupExperiment()

        # set the start values
        fmu.setReal(vr=start_vrs, value=start_values)

        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        time = 0.0
        step_size = 1e-4

        results = []

        # simulation loop
        while time < stop_time:
            fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
            time += step_size

            if time > 0.02:
                result = fmu.getReal(result_vrs)
                results.append(result)

        u_dc, losses = zip(*results)

        # store the index and the averaged signals
        zipped.append((i, [np.average(u_dc), np.average(losses)]))

    fmu.terminate()

    # call the FMI API directly to avoid unloading the share library
    fmu.fmi2FreeInstance(fmu.component)

    if sync:
        # remember the shared library handle so we can unload it later
        global dll_handle
        dll_handle = fmu.dll._handle
    else:
        # unload the shared library directly
        fmpy.freeLibrary(fmu.dll._handle)

    return zipped


def run_experiment(show_plot=True):

    if platform not in ['win32', 'win64']:
        raise Exception("Rectifier.fmu is only available for Windows")

    print("Parameter variation on %s:" % fmu_filename)
    print("  VAC", v_ac)
    print("  IDC", i_dc)

    if sync:
        dask.config.set(scheduler='synchronous')  # synchronized scheduler

    # download the FMU
    download_test_file('2.0', 'CoSimulation', 'Dymola', '2017', 'Rectifier', fmu_filename)

    # read the model description
    model_description = read_model_description(fmu_filename)

    # collect the value references for the variables to read / write
    vrs = {}
    for variable in model_description.modelVariables:
        vrs[variable.name] = variable.valueReference

    # extract the FMU
    unzipdir = fmpy.extract(fmu_filename)

    fmu_args = {'guid': model_description.guid,
                'modelIdentifier': model_description.coSimulation.modelIdentifier,
                'unzipDirectory': unzipdir}

    # get the value references for the start and output values
    start_vrs = [vrs['VAC'], vrs['IDC']]
    result_vrs = [vrs['uDC'], vrs['Losses']]

    indices = list(np.ndindex(I_DC.shape))

    print("Running %d simulations (%d chunks)..." % (V_AC.size, n_chunks))
    with ProgressBar():
        # calculate the losses for every chunk
        b = bag.from_sequence(indices, npartitions=n_chunks)
        results = b.map_partitions(simulate_fmu, fmu_args, start_vrs, result_vrs).compute()

    LOSSES = np.zeros_like(V_AC)

    # put the results together
    for i, res in results:
        LOSSES[i] = res[1]

    # unload the shared library
    if sync:
        while True:
            try:
                fmpy.freeLibrary(dll_handle)
            except:
                break

    # clean up
    shutil.rmtree(unzipdir, ignore_errors=True)

    if show_plot:
        print("Plotting results...")

        import matplotlib.pyplot as plt

        figure = plt.figure()
        figure.patch.set_facecolor('white')
        ax = figure.add_subplot(1, 1, 1)

        CS = plt.contourf(V_AC, I_DC, LOSSES, 10)
        plt.colorbar(CS, aspect=30)

        CS = ax.contour(V_AC, I_DC, LOSSES, 10, colors='k', linewidths=0.8)
        ax.clabel(CS=CS, fmt='%.0f', fontsize=9, inline=1)

        ax.set_title('Losses / W')
        ax.set_xlabel('AC Voltage / V')
        ax.set_ylabel('DC Current / A')

        plt.show()
    else:
        print("Plotting disabled")

    print("Done.")

    return LOSSES


if __name__ == '__main__':

    run_experiment()
