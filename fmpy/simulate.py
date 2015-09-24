import shutil
from tempfile import mkdtemp
import numpy as np
from fmpy import *
import sys
import zipfile

def simulate(filename, start_time=0, stop_time=1, step_size=1e-3, start_values={}):

    time = start_time

    unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform == 'win32':
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    with zipfile.ZipFile(filename, 'r') as fmufile:
        fmufile.extractall(unzipdir)

    fmu = FMU2(unzipdir=unzipdir)

    names = fmu.variableNames

    vr = (fmi2ValueReference * len(names))()

    for i, name in enumerate(names):
        vr[i] = fmu.variables[name].valueReference

    fmu.instantiate('model', fmi2CoSimulation)
    fmu.setupExperiment(tolerance=None, startTime=time)



    for name, value in start_values.items():
        sv = fmu.variables[name]
        valueReference = (fmi2ValueReference * 1)(sv.valueReference)
        value = (fmi2Real * 1)(value)
        fmu.setReal(valueReference, value)

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    result = []

    while time < stop_time:
        status = fmu.doStep(time, step_size, fmi2True)
        result.append(tuple([time] + fmu.getReal(vr)))
        time += step_size

    fmu.terminate()
    fmu.freeInstance()

    shutil.rmtree(unzipdir)

    dt = np.dtype([('time', np.float64)] + zip(names, [np.float64] * len(names)))

    return np.array(result, dtype=dt)
