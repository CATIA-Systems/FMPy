
""" This example demonstrates how to save CPU time by reusing the extracted FMU,
 loaded model description, and FMU instance when simulating the same FMU multiple times """

from fmpy import *
from fmpy.util import download_file
import shutil

epsilon = 0.001 # tolerance for subsequent states
def run_efficient_loop_with_state():

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

    tau = 10. # fun fact: found the exact period by chance!
    start_time = 0.
    stop_time = start_time + tau
    # perform the iteration
    initialize = True
    first = None
    last = None
    # reset the FMU instance instead of creating a new one
    fmu_instance.reset()
    for i in range(100):
        # pass the unzipdir, model description and FMU instance to simulate_fmu()
        result = simulate_fmu(  
            unzipdir,
            start_time = start_time,
            stop_time = stop_time,
            model_description=model_description,
            fmu_instance=fmu_instance,
            initialize = initialize,
        )
        initialize = False               
        start_time = stop_time
        stop_time = stop_time + tau
        # check that the state is propagated correctly
        if not last is None:
            if not ((result[0]["x0"] - last["x0"]) < epsilon):
                raise Exception("new start state has to equal old last state")
            if not ((result[0]["x1"] - last["x1"]) < epsilon):
                raise Exception("new start state has to equal old last state")
            if not ((result[0]["time"] - last["time"]) < epsilon):
                raise Exception("new start state has to equal old last state")
        # check that the initial state changes over time
        if not first is None:
            if (first["x0"] - result[0]["x0"] < epsilon) and (first["x1"] - result[0]["x1"] < epsilon):
                raise Exception("initial state is expected to be not stale")
        first = result[0]
        last = result[-1]
       
    # free the FMU instance and unload the shared library
    fmu_instance.terminate()
    fmu_instance.freeInstance()

    # delete the temporary directory
    shutil.rmtree(unzipdir, ignore_errors=True)


if __name__ == '__main__':
    run_efficient_loop_with_state()