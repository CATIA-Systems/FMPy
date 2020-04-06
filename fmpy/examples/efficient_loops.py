""" This example demonstrates how to save CPU time by reusing the extracted FMU,
 loaded model description, and FMU instance when simulating the same FMU multiple times """

from fmpy import *
from fmpy.util import download_file
import shutil


def run_efficient_loop():

    # download the FMU
    url = 'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win64/Test-FMUs/0.0.2/VanDerPol/VanDerPol.fmu'
    sha = 'a870f5f7f712e8152bfd60a1c2fd1c0bc10d4ca8124bd3031e321e8dd1e71bb0'
    download_file(url, sha)

    # extract the FMU to a temporary directory
    unzipdir = extract('VanDerPol.fmu')

    # read the model description
    model_description = read_model_description(unzipdir)

    # instantiate the FMU
    fmu_instance = instantiate_fmu(unzipdir, model_description, 'ModelExchange')

    # perform the iteration
    for i in range(100):

        # reset the FMU instance instead of creating a new one
        fmu_instance.reset()

        # calculate the parameters for this run
        start_values = {'mu': i * 0.01}

        # pass the unzipdir, model description and FMU instance to simulate_fmu()
        result = simulate_fmu(unzipdir,
                              start_values=start_values,
                              model_description=model_description,
                              fmu_instance=fmu_instance)

    # free the FMU instance and unload the shared library
    fmu_instance.freeInstance()

    # delete the temporary directory
    shutil.rmtree(unzipdir, ignore_errors=True)


if __name__ is '__main__':
    run_efficient_loop()
