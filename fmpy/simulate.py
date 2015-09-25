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

    start = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

    for name, value in start_values.items():
        sv = fmu.variables[name]
        # TODO: add start values from xml
        start[sv.type].append((sv.valueReference, sv.start))

    if len(start['Real']) > 0:
        vrs, values = zip(*start['Real'])
        status = fmu.fmi2SetReal(fmu.component, (fmi2ValueReference * len(vrs))(*vrs), len(vrs), (fmi2Real * len(values))(*values))

    if len(start['Integer']) > 0:
        vrs, values = zip(*start['Integer'])
        status = fmu.fmi2SetInteger(fmu.component, (fmi2ValueReference * len(vrs))(*vrs), len(vrs), (fmi2Integer * len(values))(*values))

    if len(start['Boolean']) > 0:
        vrs, values = zip(*start['Boolean'])
        status = fmu.fmi2SetBoolean(fmu.component, (fmi2ValueReference * len(vrs))(*vrs), len(vrs), (fmi2Boolean * len(values))(*values))

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    cols = [('time', np.float64)]
    result = []

    values = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

    for name, sv in fmu.variables.items():
        values[sv.type].append((name, sv.valueReference))

    if len(values['Real']) > 0:
        real_names, real_vrs = zip(*values['Real'])
        real_vrs = (fmi2ValueReference * len(real_vrs))(*real_vrs)
        real_values = (fmi2Real * len(real_vrs))()
        cols += zip(real_names, [np.float64] * len(real_names))
    else:
        real_vrs = []

    if len(values['Integer']) > 0:
        integer_names, integer_vrs = zip(*values['Integer'])
        integer_vrs = (fmi2ValueReference * len(integer_vrs))(*integer_vrs)
        integer_values = (fmi2Integer * len(integer_vrs))()
        cols += zip(integer_names, [np.int32] * len(integer_names))
    else:
        integer_vrs = []

    if len(values['Boolean']) > 0:
        boolean_names, boolean_vrs = zip(*values['Boolean'])
        boolean_vrs = (fmi2ValueReference * len(boolean_vrs))(*boolean_vrs)
        boolean_values = (fmi2Boolean * len(boolean_vrs))()
        cols += zip(boolean_names, [np.int32] * len(boolean_names))
    else:
        boolean_vrs = []

    while time < stop_time:
        row =[time]

        if len(real_vrs) > 0:
            status = fmu.fmi2GetReal(fmu.component, real_vrs, len(real_vrs), real_values)
            row += list(real_values)

        if len(integer_vrs) > 0:
            status = fmu.fmi2GetInteger(fmu.component, integer_vrs, len(integer_vrs), integer_values)
            row += list(integer_values)

        if len(boolean_vrs) > 0:
            status = fmu.fmi2GetBoolean(fmu.component, boolean_vrs, len(boolean_vrs), boolean_values)
            row += list(boolean_values)

        result.append(tuple(row))
        status = fmu.doStep(time, step_size, fmi2True)
        time += step_size

    fmu.terminate()
    fmu.freeInstance()

    shutil.rmtree(unzipdir)

    dt = np.dtype(cols)

    return np.array(result, dtype=np.dtype(cols))
