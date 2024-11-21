""" This example demonstrates how continue a simulation e.g. to
 retrieve outputs or set tunable parameters at certain intervals while
 keeping the FMU instance alive. """

import os
import tempfile
import shutil
import numpy as np
from fmpy import extract, read_model_description, instantiate_fmu, simulate_fmu, plot_result
from fmpy.simulation import apply_start_values
from fmpy.util import download_file


def continue_simulation(fmu_filename):

    # extract the FMU to a temporary directory
    unzipdir = extract(fmu_filename)

    # read the model description
    model_description = read_model_description(unzipdir)

    # instantiate the FMU beforehand, so we can keep it alive
    fmu_instance = instantiate_fmu(unzipdir=unzipdir, model_description=model_description)

    # simulate to 1 s
    result1 = simulate_fmu(
        filename=unzipdir,
        model_description=model_description,
        fmu_instance=fmu_instance,
        start_values={'e': 0.95},
        stop_time=1,
        set_stop_time=False,  # don't communicate the stop time, so we can continue
        terminate=False  # keep the FMU instance alive
    )

    # change a tunable parameter
    apply_start_values(fmu=fmu_instance, model_description=model_description, start_values={'e': 0.55})

    # continue to 2 s
    result2 = simulate_fmu(
        filename=unzipdir,
        model_description=model_description,
        fmu_instance=fmu_instance,
        initialize=False,  # the FMU instance is already initialized
        start_time=1,  # start where we left off
        stop_time=2,
        terminate=False
    )

    # concatenate and plot the results
    plot_result(np.concatenate((result1, result2)), events=True)

    # clean up
    fmu_instance.terminate()
    fmu_instance.freeInstance()
    shutil.rmtree(unzipdir)


if __name__ == '__main__':

    archive_filename = download_file(
        url='https://github.com/modelica/Reference-FMUs/releases/download/v0.0.23/Reference-FMUs-0.0.23.zip',
        checksum='d6ad6fc08e53053fe413540016552387257971261f26f08a855f9a6404ef2991'
    )

    with tempfile.TemporaryDirectory() as tempdir:

        extract(archive_filename, unzipdir=tempdir)

        # works also for '1.0/cs' and '2.0'
        continue_simulation(os.path.join(tempdir, '3.0', 'BouncingBall.fmu'))
