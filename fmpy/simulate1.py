# noinspection PyPep8

import shutil
from tempfile import mkdtemp
import numpy as np
from fmpy.fmi1 import *
import sys
import zipfile
from .modelDescription import read_model_description


def simulate(filename, start_time=0, stop_time=1, step_size=1e-3, start_values={}, output=None):

    md = read_model_description(filename)

    time = start_time

    unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform == 'win32':
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    with zipfile.ZipFile(filename, 'r') as fmufile:
        fmufile.extractall(unzipdir)

    if md.fmiVersion == '1.0':
        fmu = FMU1(modelDescription=md, unzipDirectory=unzipdir, instanceName="instance1")
        fmu.instantiate("rectifier1")
        fmu.initializeSlave()
        pass

    cols = [('time', np.float64)]
    result = []

    values = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

    for sv in md.modelVariables:
        if (output is None and sv.causality == 'output') or (output is not None and sv.name in output):
            values[sv.type].append((sv.name, sv.valueReference))

    if len(values['Real']) > 0:
        real_names, real_vrs = zip(*values['Real'])
        real_vrs = (fmi1ValueReference * len(real_vrs))(*real_vrs)
        real_values = (fmi1Real * len(real_vrs))()
        cols += zip(real_names, [np.float64] * len(real_names))
    else:
        real_vrs = []

    if len(values['Integer']) > 0:
        integer_names, integer_vrs = zip(*values['Integer'])
        integer_vrs = (fmi1ValueReference * len(integer_vrs))(*integer_vrs)
        integer_values = (fmi1Integer * len(integer_vrs))()
        cols += zip(integer_names, [np.int32] * len(integer_names))
    else:
        integer_vrs = []

    if len(values['Boolean']) > 0:
        boolean_names, boolean_vrs = zip(*values['Boolean'])
        boolean_vrs = (fmi1ValueReference * len(boolean_vrs))(*boolean_vrs)
        boolean_values = (fmi1Boolean * len(boolean_vrs))()
        cols += zip(boolean_names, [np.int32] * len(boolean_names))
    else:
        boolean_vrs = []


    while time < stop_time:

        row = [time]

        if len(real_vrs) > 0:
            status = fmu.fmi1GetReal(fmu.component, real_vrs, len(real_vrs), real_values)
            row += list(real_values)

        if len(integer_vrs) > 0:
            status = fmu.fmi1GetInteger(fmu.component, integer_vrs, len(integer_vrs), integer_values)
            row += list(integer_values)

        if len(boolean_vrs) > 0:
            status = fmu.fmi1GetBoolean(fmu.component, boolean_vrs, len(boolean_vrs), boolean_values)
            row += list(boolean_values)

        result.append(tuple(row))

        status = fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)

        time += step_size

    # clean up
    fmu.terminateSlave()
    fmu.freeSlaveInstance()
    shutil.rmtree(unzipdir)

    # return the result
    return np.array(result, dtype=np.dtype(cols))
