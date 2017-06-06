# noinspection PyPep8

import shutil
import zipfile
from tempfile import mkdtemp
from fmpy.model_description import read_model_description
from .fmi1 import *
from .fmi2 import *
from . import CO_SIMULATION, MODEL_EXCHANGE
import numpy as np
from scipy import interpolate
import sys


class Recorder(object):

    def __init__(self, fmu, variableNames=None, interval=None):

        self.fmu = fmu
        self.interval = interval

        md = fmu.modelDescription

        is_fmi1 =  md.fmiVersion == '1.0'

        if is_fmi1:
            self._getReal = fmu.fmi1GetReal
            self._getInteger = fmu.fmi1GetInteger
            self._getBoolean = fmu.fmi1GetBoolean
            self._bool_type = fmi1Boolean
        else:
            self._getReal = fmu.fmi2GetReal
            self._getInteger = fmu.fmi2GetInteger
            self._getBoolean = fmu.fmi2GetBoolean
            self._bool_type = fmi2Boolean

        self.cols = [('time', np.float64)]
        self.rows = []

        self.values = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

        for sv in md.modelVariables:
            if (variableNames is None and sv.causality == 'output') or (variableNames is not None and sv.name in variableNames):
                self.values['Integer' if sv.type == 'Enumeration' else sv.type].append((sv.name, sv.valueReference))

        if len(self.values['Real']) > 0:
            real_names, real_vrs = zip(*self.values['Real'])
            self.real_vrs = (c_uint32 * len(real_vrs))(*real_vrs)
            self.real_values = (c_double * len(real_vrs))()
            self.cols += zip(real_names, [np.float64] * len(real_names))
        else:
            self.real_vrs = []

        if len(self.values['Integer']) > 0:
            integer_names, integer_vrs = zip(*self.values['Integer'])
            self.integer_vrs = (c_uint32 * len(integer_vrs))(*integer_vrs)
            self.integer_values = (c_int32 * len(integer_vrs))()
            self.cols += zip(integer_names, [np.int32] * len(integer_names))
        else:
            self.integer_vrs = []

        if len(self.values['Boolean']) > 0:
            boolean_names, boolean_vrs = zip(*self.values['Boolean'])
            self. boolean_vrs = (c_uint32 * len(boolean_vrs))(*boolean_vrs)
            self.boolean_values = ((c_int8 if is_fmi1 else c_int32) * len(boolean_vrs))()
            self.cols += zip(boolean_names, ([np.int8] if is_fmi1 else [np.int32]) * len(boolean_names))
        else:
            self.boolean_vrs = []

    def sample(self, time, force = False):

        if not force and self.interval is not None and len(self.rows) > 0:
            last = self.rows[-1][0]
            if time - last < self.interval:
                return

        row = [time]

        if len(self.real_vrs) > 0:
            status = self._getReal(self.fmu.component, self.real_vrs, len(self.real_vrs), self.real_values)
            row += list(self.real_values)

        if len(self.integer_vrs) > 0:
            status = self._getInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)
            row += list(self.integer_values)

        if len(self.boolean_vrs) > 0:
            status = self._getBoolean(self.fmu.component, self.boolean_vrs, len(self.boolean_vrs),
                                      cast(self.boolean_values, POINTER(self._bool_type)))
            row += list(self.boolean_values)

        self.rows.append(tuple(row))

    def result(self):
        return np.array(self.rows, dtype=np.dtype(self.cols))


class Input(object):

    def __init__(self, fmu, signals):

        self.fmu = fmu
        self.signals = signals

        if signals is None:
            return

        is_fmi1 = fmu.modelDescription.fmiVersion == '1.0'

        # get the setters
        if is_fmi1:
            self._setReal = fmu.fmi1SetReal
            self._setInteger = fmu.fmi1SetInteger
            self._setBoolean = fmu.fmi1SetBoolean
            self._bool_type = fmi1Boolean
        else:
            self._setReal = fmu.fmi2SetReal
            self._setInteger = fmu.fmi2SetInteger
            self._setBoolean = fmu.fmi2SetBoolean
            self._bool_type = fmi2Boolean

        self.values = {'Real': [], 'Integer': [], 'Boolean': [], 'String': []}

        for sv in fmu.modelDescription.modelVariables:

            if sv.name is None:
                continue

            if sv.causality == 'input':
                if not sv.name in self.signals.dtype.names:
                    print("Warning: missing input for " + sv.name)
                    continue
                f = interpolate.interp1d(self.signals['time'], self.signals[sv.name], kind='linear' if sv.type == 'Real' else 'zero')
                self.values['Integer' if sv.type == 'Enumeration' else sv.type].append((f, sv.valueReference))

        if len(self.values['Real']) > 0:
            self.real_fun, real_vrs = zip(*self.values['Real'])
            self.real_vrs = (c_uint32 * len(real_vrs))(*real_vrs)
            self.real_values = (c_double * len(real_vrs))()
        else:
            self.real_vrs = []

        if len(self.values['Integer']) > 0:
            self.integer_fun, integer_vrs = zip(*self.values['Integer'])
            self.integer_vrs = (c_uint32 * len(integer_vrs))(*integer_vrs)
            self.integer_values = (c_int32 * len(integer_vrs))()
        else:
            self.integer_vrs = []

        if len(self.values['Boolean']) > 0:
            self.boolean_fun, boolean_vrs = zip(*self.values['Boolean'])
            self.boolean_vrs = (c_uint32 * len(boolean_vrs))(*boolean_vrs)
            self.boolean_values = ((c_int8 if is_fmi1 else c_int32) * len(boolean_vrs))()
        else:
            self.boolean_vrs = []

    def apply(self, time):

        if self.signals is None:
            return

        if len(self.real_vrs) > 0:
            for i, f in enumerate(self.real_fun):
                self.real_values[i] = f(time)
            status = self._setReal(self.fmu.component, self.real_vrs, len(self.real_vrs), self.real_values)

        if len(self.integer_vrs) > 0:
            #status = self.fmu.fmi1GetInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)
            #print(time, self.integer_values[0], status)

            for i, f in enumerate(self.integer_fun):
                self.integer_values[i] = f(time)
            status = self._setInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)
            #print(time, f(time), self.integer_values[0], status)

        if len(self.boolean_vrs) > 0:
            for i, f in enumerate(self.boolean_fun):
                self.boolean_values[i] = f(time)
            status = self._setBoolean(self.fmu.component, self.boolean_vrs, len(self.boolean_vrs),
                                      cast(self.boolean_values, POINTER(self._bool_type)))
            # print(time, f(time), self.boolean_values[0], status)


def simulate_fmu(filename, validate=True, start_time=None, stop_time=None, step_size=None, sample_interval=None, fmi_type=None, start_values={}, input=None, output=None):

    modelDescription = read_model_description(filename, validate=validate)

    if fmi_type is None:
        # determine the FMI type automatically
        fmi_type = CO_SIMULATION if modelDescription.coSimulation is not None else MODEL_EXCHANGE

    defaultExperiment = modelDescription.defaultExperiment

    if start_time is None:
        if defaultExperiment is not None and defaultExperiment.startTime is not None:
            start_time = defaultExperiment.startTime
        else:
            start_time = 0.0

    if stop_time is None:
        if defaultExperiment is not None:
            stop_time = defaultExperiment.stopTime
        else:
            stop_time = 1.0

    if step_size is None:
        total_time = stop_time - start_time
        step_size = 10 ** (np.round(np.log10(0.09)) - 3)

    unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform == 'win32':
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    with zipfile.ZipFile(filename, 'r') as fmufile:
        fmufile.extractall(unzipdir)

    if modelDescription.fmiVersion == '1.0':
        simfun = simulateME1 if fmi_type is MODEL_EXCHANGE else simulateCS1
    else:
        simfun = simulateME2 if fmi_type is MODEL_EXCHANGE else simulateCS2

    if sample_interval is None:
        sample_interval = (stop_time - start_time) / 500

    # simulate_fmu the FMU
    result = simfun(modelDescription, unzipdir, start_time, stop_time, step_size, input, output, sample_interval)

    # clean up
    shutil.rmtree(unzipdir)

    return result


def simulateME1(modelDescription, unzipdir, start_time, stop_time, step_size, input_signals, output, output_interval):

    fmu = FMU1Model(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate()

    time = start_time

    fmu.setTime(time)

    input = Input(fmu, input_signals)

    input.apply(time)

    fmu.initialize()

    recorder = Recorder(fmu=fmu, variableNames=output, interval=output_interval)

    prez  = np.zeros_like(fmu.z)

    while time < stop_time:

        input.apply(time)

        fmu.getContinuousStates()
        fmu.getDerivatives()

        tPre = time;
        time = min(time + step_size, stop_time);

        timeEvent = fmu.eventInfo.upcomingTimeEvent != fmi1False and fmu.eventInfo.nextEventTime <= time;

        if timeEvent:
            time = fmu.eventInfo.nextEventTime

        dt = time - tPre

        fmu.setTime(time)

        # forward Euler
        fmu.x += dt * fmu.dx

        fmu.setContinuousStates()

        # check for step event, e.g.dynamic state selection
        stepEvent = fmu.completedIntegratorStep()

        # check for state event
        prez[:] = fmu.z
        fmu.getEventIndicators()
        stateEvent = np.any((prez * fmu.z) < 0)

        # handle events
        if timeEvent or stateEvent or stepEvent:
            fmu.eventUpdate()

        recorder.sample(time)

    recorder.sample(time, force=True)

    fmu.terminate()
    fmu.freeInstance()

    return recorder.result()


def simulateCS1(modelDescription, unzipdir, start_time, stop_time, step_size, input_signals, output, output_interval):

    fmu = FMU1Slave(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate("instance1")
    fmu.initialize()

    input = Input(fmu, input_signals)

    recorder = Recorder(fmu=fmu, variableNames=output, interval=output_interval)

    time = start_time

    while time < stop_time:
        recorder.sample(time)
        input.apply(time)
        status = fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        time += step_size

    recorder.sample(time, force=True)

    fmu.terminate()
    fmu.freeInstance()

    return recorder.result()


def simulateME2(modelDescription, unzipdir, start_time, stop_time, step_size, input_signals, output, output_interval):

    fmu = FMU2Model(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate()
    fmu.setupExperiment(tolerance=None, startTime=start_time)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    # event iteration
    fmu.eventInfo.newDiscreteStatesNeeded = fmi2True
    fmu.eventInfo.terminateSimulation = fmi2False

    while fmu.eventInfo.newDiscreteStatesNeeded == fmi2True and fmu.eventInfo.terminateSimulation == fmi2False:
        # update discrete states
        status = fmu.newDiscreteStates()

    fmu.enterContinuousTimeMode()

    input = Input(fmu, input_signals)

    recorder = Recorder(fmu=fmu, variableNames=output, interval=output_interval)

    prez  = np.zeros_like(fmu.z)

    time = start_time

    recorder.sample(time)

    while time < stop_time:

        fmu.getContinuousStates()
        fmu.getDerivatives()

        tPre = time
        time = min(time + step_size, stop_time)

        input.apply(time)

        timeEvent = fmu.eventInfo.nextEventTimeDefined != fmi2False and fmu.eventInfo.nextEventTime <= time

        if timeEvent:
            time = fmu.eventInfo.nextEventTime

        dt = time - tPre

        fmu.setTime(time)

        # forward Euler
        fmu.x += dt * fmu.dx

        fmu.setContinuousStates()

        # check for state event
        prez[:] = fmu.z
        fmu.getEventIndicators()
        stateEvent = np.any((prez * fmu.z) < 0)

        # check for step event
        stepEvent, terminateSimulation = fmu.completedIntegratorStep()

        if timeEvent or stateEvent or stepEvent != fmi2False:

            # handle events
            fmu.enterEventMode()

            fmu.eventInfo.newDiscreteStatesNeeded = fmi2True
            fmu.eventInfo.terminateSimulation = fmi2False

            # update discrete states
            while fmu.eventInfo.newDiscreteStatesNeeded != fmi2False and fmu.eventInfo.terminateSimulation == fmi2False:
                fmu.newDiscreteStates()

            fmu.enterContinuousTimeMode()

        recorder.sample(time)

    recorder.sample(time, force=True)

    fmu.terminate()
    fmu.freeInstance()

    return recorder.result()


def simulateCS2(modelDescription, unzipdir, start_time, stop_time, step_size, input_signals, output, output_interval):

    fmu = FMU2Slave(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate()
    fmu.setupExperiment(tolerance=None, startTime=start_time)
    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    input = Input(fmu, input_signals)

    recorder = Recorder(fmu=fmu, variableNames=output, interval=output_interval)

    time = start_time

    while time < stop_time:
        recorder.sample(time)
        input.apply(time)
        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        time += step_size

    recorder.sample(time, force=True)

    fmu.terminate()
    fmu.freeInstance()

    return recorder.result()
