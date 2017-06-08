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

        self.cols = [('time', np.float64)]
        self.rows = []

        real_names = []
        self.real_vrs = []

        integer_names = []
        self.integer_vrs = []

        boolean_names = []
        self.boolean_vrs = []

        for sv in fmu.modelDescription.modelVariables:

            if (variableNames is None and sv.causality == 'output') or (variableNames is not None and sv.name in variableNames):

                if sv.type == 'Real':
                    real_names.append(sv.name)
                    self.real_vrs.append(sv.valueReference)
                elif sv.type in ['Integer', 'Enumeration']:
                    integer_names.append(sv.name)
                    self.integer_vrs.append(sv.valueReference)
                elif sv.type == 'Boolean':
                    boolean_names.append(sv.name)
                    self.boolean_vrs.append(sv.valueReference)

        self.cols += zip(real_names, [np.float64] * len(real_names))
        self.cols += zip(integer_names, [np.int32] * len(integer_names))
        self.cols += zip(boolean_names, [np.int32] * len(boolean_names))

    def sample(self, time, force = False):

        if not force and self.interval is not None and len(self.rows) > 0:
            last = self.rows[-1][0]
            if time - last < self.interval:
                return

        row = [time]

        if self.real_vrs:
            row += self.fmu.getReal(self.real_vrs)

        if self.integer_vrs:
            row += self.fmu.getInteger(self.integer_vrs)

        if self.boolean_vrs:
            row += self.fmu.getBoolean(self.boolean_vrs)

        self.rows.append(tuple(row))

    def result(self):
        return np.array(self.rows, dtype=np.dtype(self.cols))


class Input(object):

    def __init__(self, fmu, signals):

        self.fmu = fmu
        self.signals = signals

        self.real_vrs = []
        self.real_fun = []

        self.integer_vrs = []
        self.integer_fun = []

        self.boolean_vrs = []
        self.boolean_fun = []

        for sv in fmu.modelDescription.modelVariables:

            if sv.name is None:
                continue # TODO: why does this happen?

            if sv.causality == 'input':

                if not sv.name in self.signals.dtype.names:
                    print("Warning: missing input for " + sv.name)
                    continue

                # TODO: use zero-hold for discrete Reals
                f = interpolate.interp1d(self.signals['time'], self.signals[sv.name], kind='linear' if sv.type == 'Real' else 'zero')

                if sv.type == 'Real':
                    self.real_vrs.append(sv.valueReference)
                    self.real_fun.append(f)
                elif sv.type in ['Integer', 'Enumeration']:
                    self.integer_vrs.append(sv.valueReference)
                    self.integer_fun.append(f)
                elif sv.type == 'Boolean':
                    self.boolean_vrs.append(sv.valueReference)
                    self.boolean_fun.append(f)

    def apply(self, time):

        if self.real_fun:
            self.fmu.setReal(self.real_vrs, map(lambda f: f(time), self.real_fun))

        if self.integer_fun:
            self.fmu.setInteger(self.integer_vrs, map(lambda f: f(time), self.integer_fun))

        if self.boolean_fun:
            self.fmu.setBoolean(self.boolean_vrs, map(lambda f: f(time), self.boolean_fun))


def apply_start_values(fmu, start_values):

    for sv in fmu.modelDescription.modelVariables:

        if sv.name in start_values:

            vr = sv.valueReference
            value = start_values[sv.name]

            if sv.type == 'Real':
                fmu.setReal([vr], [value])
            elif sv.type in ['Integer', 'Enumeration']:
                fmu.setInteger([vr], [value])
            elif sv.type == 'Boolean':
                fmu.setBoolean([vr], [value])
            elif sv.type == 'String':
                pass # TODO: implement this


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
    if sys.platform.startswith('win'):
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
    result = simfun(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input, output, sample_interval)

    # clean up
    shutil.rmtree(unzipdir)

    return result


def simulateME1(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval):

    fmu = FMU1Model(modelDescription=modelDescription, unzipDirectory=unzipdir)

    fmu.instantiate()

    time = start_time

    fmu.setTime(time)

    apply_start_values(fmu, start_values)

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


def simulateCS1(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval):

    fmu = FMU1Slave(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate("instance1")

    apply_start_values(fmu, start_values)

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


def simulateME2(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval):

    fmu = FMU2Model(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate()
    fmu.setupExperiment(tolerance=None, startTime=start_time)

    apply_start_values(fmu, start_values)

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


def simulateCS2(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval):

    fmu = FMU2Slave(modelDescription=modelDescription, unzipDirectory=unzipdir)
    fmu.instantiate()
    fmu.setupExperiment(tolerance=None, startTime=start_time)

    apply_start_values(fmu, start_values)

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    input = Input(fmu, input_signals)

    recorder = Recorder(fmu=fmu, variableNames=output, interval=output_interval)

    time = start_time

    while time < stop_time:
        recorder.sample(time)
        input.apply(time)
        #print(time)
        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
        time += step_size

    recorder.sample(time, force=True)

    fmu.terminate()
    fmu.freeInstance()

    return recorder.result()
