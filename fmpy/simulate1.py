# noinspection PyPep8

import shutil
from tempfile import mkdtemp
import numpy as np
from fmpy.fmi1 import *
import sys
import zipfile
from .modelDescription import read_model_description


class Recorder(object):

    def __init__(self, fmu, output=None):

        self.fmu = fmu

        md = fmu.modelDescription

        self.cols = [('time', np.float64)]
        self.rows = []

        self.values = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

        for sv in md.modelVariables:
            if (output is None and sv.causality == 'output') or (output is not None and sv.name in output):
                self.values[sv.type].append((sv.name, sv.valueReference))

        if len(self.values['Real']) > 0:
            real_names, real_vrs = zip(*self.values['Real'])
            self.real_vrs = (fmi1ValueReference * len(real_vrs))(*real_vrs)
            self.real_values = (fmi1Real * len(real_vrs))()
            self.cols += zip(real_names, [np.float64] * len(real_names))
        else:
            self.real_vrs = []

        if len(self.values['Integer']) > 0:
            integer_names, integer_vrs = zip(*self.values['Integer'])
            self.integer_vrs = (fmi1ValueReference * len(integer_vrs))(*integer_vrs)
            self.integer_values = (fmi1Integer * len(integer_vrs))()
            self.cols += zip(integer_names, [np.int32] * len(integer_names))
        else:
            self.integer_vrs = []

        if len(self.values['Boolean']) > 0:
            boolean_names, boolean_vrs = zip(*self.values['Boolean'])
            self. boolean_vrs = (fmi1ValueReference * len(boolean_vrs))(*boolean_vrs)
            self.boolean_values = (fmi1Boolean * len(boolean_vrs))()
            self.cols += zip(boolean_names, [np.int32] * len(boolean_names))
        else:
            self.boolean_vrs = []

    def sample(self, time):

        row = [time]

        if len(self.real_vrs) > 0:
            status = self.fmu.fmi1GetReal(self.fmu.component, self.real_vrs, len(self.real_vrs), self.real_values)
            row += list(self.real_values)

        if len(self.integer_vrs) > 0:
            status = self.fmu.fmi1GetInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)
            row += list(self.integer_values)

        if len(self.boolean_vrs) > 0:
            status = self.fmu.fmi1GetBoolean(self.fmu.component, self.boolean_vrs, len(self.boolean_vrs), self.boolean_values)
            row += list(self.boolean_values)

        self.rows.append(tuple(row))

    def result(self):
        return np.array(self.rows, dtype=np.dtype(self.cols))


def simulate(filename, start_time=0, stop_time=1, step_size=1e-3, start_values={}, output=None):

    modelDescription = read_model_description(filename)

    time = start_time

    unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform == 'win32':
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    with zipfile.ZipFile(filename, 'r') as fmufile:
        fmufile.extractall(unzipdir)

    if modelDescription.fmiVersion == '1.0':
        fmu = FMU1Slave(modelDescription=modelDescription, unzipDirectory=unzipdir, instanceName="instance1")
        fmu.instantiate("rectifier1")
        fmu.initializeSlave()
        pass

    recorder = Recorder(fmu=fmu, output=output)

    while time < stop_time:
        recorder.sample(time)
        status = fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        time += step_size

    # clean up
    fmu.terminateSlave()
    fmu.freeSlaveInstance()
    shutil.rmtree(unzipdir)

    return recorder.result()
