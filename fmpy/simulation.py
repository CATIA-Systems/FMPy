# noinspection PyPep8

import shutil
from fmpy.model_description import read_model_description
from .fmi1 import *
from .fmi1 import _FMU1
from .fmi2 import *
from . import extract
import numpy as np
from time import time as current_time


class Recorder(object):

    def __init__(self, fmu, modelDescription, variableNames=None, interval=None):

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

        for sv in modelDescription.modelVariables:

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
            row += self.fmu.getReal(vr=self.real_vrs)

        if self.integer_vrs:
            row += self.fmu.getInteger(vr=self.integer_vrs)

        if self.boolean_vrs:
            row += self.fmu.getBoolean(vr=self.boolean_vrs)

        self.rows.append(tuple(row))

    def result(self):
        return np.array(self.rows, dtype=np.dtype(self.cols))


class Input(object):

    def __init__(self, fmu, modelDescription, signals):

        self.fmu = fmu
        self.signals = signals

        if signals is None:
            return

        is_fmi1 = isinstance(fmu, _FMU1)  # fmu.modelDescription.fmiVersion == '1.0'

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

        for sv in modelDescription.modelVariables:

            if sv.name is None:
                continue

            if sv.causality == 'input':
                if sv.name not in self.signals.dtype.names:
                    print("Warning: missing input for " + sv.name)
                    continue
                self.values['Integer' if sv.type == 'Enumeration' else sv.type].append((sv.valueReference, sv.name))

        if len(self.values['Real']) > 0:
            real_vrs, self.real_names = zip(*self.values['Real'])
            self.real_vrs = (c_uint32 * len(real_vrs))(*real_vrs)
            self.real_values = (c_double * len(real_vrs))()
            self.real_table = np.stack(map(lambda n: self.signals[n], self.real_names))
        else:
            self.real_vrs = []

        if len(self.values['Integer']) > 0:
            integer_vrs, self.integer_names = zip(*self.values['Integer'])
            self.integer_vrs = (c_uint32 * len(integer_vrs))(*integer_vrs)
            self.integer_values = (c_int32 * len(integer_vrs))()
            self.integer_table = np.asarray(np.stack(map(lambda n: self.signals[n], self.integer_names)), dtype=np.int32)
        else:
            self.integer_vrs = []

        if len(self.values['Boolean']) > 0:
            boolean_vrs, self.boolean_names = zip(*self.values['Boolean'])
            self.boolean_vrs = (c_uint32 * len(boolean_vrs))(*boolean_vrs)
            self.boolean_values = ((c_int8 if is_fmi1 else c_int32) * len(boolean_vrs))()
            self.boolean_table = np.asarray(np.stack(map(lambda n: self.signals[n], self.boolean_names)), dtype=np.int32)
        else:
            self.boolean_vrs = []

    def apply(self, time, continuous=True, discrete=True):

        if self.signals is None:
            return

        t = self.signals['time']

        # find the left insert index
        i0 = np.searchsorted(t, time)

        # TODO: check for event

        if len(self.real_vrs) > 0 and continuous:
            self.real_values[:] = self.interpolate(time=time, t=t, table=self.real_table)
            self._setReal(self.fmu.component, self.real_vrs, len(self.real_vrs), self.real_values)

        # TODO: discrete apply Reals

        if len(self.integer_vrs) > 0 and discrete:
            self.integer_values[:] = self.interpolate(time=time, t=t, table=self.integer_table, discrete=True)
            self._setInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)

        if len(self.boolean_vrs) > 0 and discrete:
            self.boolean_values[:] = self.interpolate(time=time, t=t, table=self.boolean_table, discrete=True)
            self._setBoolean(self.fmu.component, self.boolean_vrs, len(self.boolean_vrs),
                                      cast(self.boolean_values, POINTER(self._bool_type)))

    @staticmethod
    def interpolate(time, t, table, discrete=False, after_event=False):

        # find the left insert index
        i0 = np.searchsorted(t, time)

        # check for event
        is_event = i0 < len(t) - 1 and t[i0] == t[i0 + 1]

        if is_event:
            if after_event:
                return table[:, i0 + 1]
            else:
                return table[:, i0]

        if i0 >= len(t):
            # extrapolate right
            i0 = len(t) - 2
        elif i0 > 0:
            # interpolate
            i0 -= 1

        # take the value after the event
        while i0 < len(t) - 1 and t[i0] == t[i0 + 1]:
            i0 += 1

        i1 = i0 + 1

        if discrete:
            return table[:, i0]

        t0 = t[i0]
        t1 = t[i1]

        w0 = (t1 - time) / (t1 - t0)
        w1 = 1 - w0

        v0 = table[:, i0]
        v1 = table[:, i1]

        # interpolate the input value
        v = w0 * v0 + w1 * v1

        return v


def apply_start_values(fmu, modelDescription, start_values):

    variables = {}

    for v in modelDescription.modelVariables:
        variables[v.name] = v

    for name, value in start_values.items():

        if name not in variables:
            raise Exception("The variable '%s' could not be set because it does not exist in the FMU." % name)

        v = variables[name]
        vr = v.valueReference

        if v.type == 'Real':
            fmu.setReal([vr], [value])
        elif v.type in ['Integer', 'Enumeration']:
            fmu.setInteger([vr], [value])
        elif v.type == 'Boolean':
            fmu.setBoolean([vr], [value])
        elif v.type == 'String':
            raise NotImplementedError("String parameters are not supported yet.")


def simulate_fmu(filename,
                 validate=True,
                 start_time=None,
                 stop_time=None,
                 step_size=None,
                 sample_interval=None,
                 fmi_type=None,
                 start_values={},
                 input=None,
                 output=None,
                 timeout=None,
                 fmi_logging=False):

    modelDescription = read_model_description(filename, validate=validate)

    if fmi_type is None:
        # determine the FMI type automatically
        fmi_type = 'CoSimulation' if modelDescription.coSimulation is not None else 'ModelExchange'

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
        step_size = 10 ** (np.round(np.log10(total_time)) - 3)

    unzipdir = extract(filename)

    if fmi_type == 'ModelExchange':
        simfun = simulateME1 if modelDescription.fmiVersion == '1.0' else simulateME2
    elif fmi_type == 'CoSimulation':
        simfun = simulateCS
    else:
        raise Exception('fmi_tpye must be either "ModelExchange" or "CoSimulation"')

    if sample_interval is None:
        sample_interval = (stop_time - start_time) / 500

    # simulate_fmu the FMU
    result = simfun(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input, output, sample_interval, timeout, fmi_logging)

    # clean up
    shutil.rmtree(unzipdir)

    return result


def simulateME1(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval, timeout, fmi_logging):

    sim_start = current_time()

    args = {'numberOfContinuousStates': modelDescription.numberOfContinuousStates,
            'numberOfEventIndicators': modelDescription.numberOfEventIndicators,
            'guid': modelDescription.guid,
            'modelIdentifier': modelDescription.modelExchange.modelIdentifier,
            'unzipDirectory': unzipdir,
            'instanceName': None,
            'logFMICalls': fmi_logging}

    fmu = FMU1Model(**args)

    fmu.instantiate()

    time = start_time

    fmu.setTime(time)

    apply_start_values(fmu, modelDescription, start_values)

    input = Input(fmu, modelDescription, input_signals)

    input.apply(time)

    fmu.initialize()

    recorder = Recorder(fmu=fmu, modelDescription=modelDescription, variableNames=output, interval=output_interval)

    prez = np.zeros_like(fmu.z)

    try:

        while time < stop_time:

            if timeout is not None and (current_time() - sim_start) > timeout:
                break

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

    except Exception as e:
        print("Simulation aborted. " + str(e))
    finally:
        fmu.freeInstance()

    return recorder.result()


def simulateME2(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval, timeout, fmi_logging):

    sim_start = current_time()

    args = {'numberOfContinuousStates': modelDescription.numberOfContinuousStates,
            'numberOfEventIndicators': modelDescription.numberOfEventIndicators,
            'guid': modelDescription.guid,
            'modelIdentifier': modelDescription.modelExchange.modelIdentifier,
            'unzipDirectory': unzipdir,
            'instanceName': None,
            'logFMICalls': fmi_logging}

    fmu = FMU2Model(**args)
    fmu.instantiate()
    fmu.setupExperiment(startTime=start_time)

    apply_start_values(fmu, modelDescription, start_values)

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    # event iteration
    fmu.eventInfo.newDiscreteStatesNeeded = fmi2True
    fmu.eventInfo.terminateSimulation = fmi2False

    while fmu.eventInfo.newDiscreteStatesNeeded == fmi2True and fmu.eventInfo.terminateSimulation == fmi2False:
        # update discrete states
        status = fmu.newDiscreteStates()

    fmu.enterContinuousTimeMode()

    input = Input(fmu, modelDescription, input_signals)

    recorder = Recorder(fmu=fmu, modelDescription=modelDescription, variableNames=output, interval=output_interval)

    prez = np.zeros_like(fmu.z)

    time = start_time

    recorder.sample(time)

    while time < stop_time:

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

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


def simulateCS(modelDescription, unzipdir, start_time, stop_time, step_size, start_values, input_signals, output, output_interval, timeout, fmi_logging):

    sim_start = current_time()

    guid = modelDescription.guid
    modelIdentifier = modelDescription.coSimulation.modelIdentifier

    args = {'guid': guid,
            'modelIdentifier': modelIdentifier,
            'unzipDirectory': unzipdir,
            'instanceName': None,
            'logFMICalls': fmi_logging}

    if modelDescription.fmiVersion == '1.0':
        fmu = FMU1Slave(**args)
        fmu.instantiate("instance1")
        apply_start_values(fmu, modelDescription, start_values)
        fmu.initialize()
    else:
        fmu = FMU2Slave(**args)
        fmu.instantiate(loggingOn=False)
        fmu.setupExperiment(tolerance=None, startTime=start_time)
        apply_start_values(fmu, modelDescription, start_values)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    input = Input(fmu=fmu, modelDescription=modelDescription, signals=input_signals)
    recorder = Recorder(fmu=fmu, modelDescription=modelDescription, variableNames=output, interval=output_interval)

    time = start_time

    try:
        while time < stop_time:
            if timeout is not None and (current_time() - sim_start) > timeout:
                break
            recorder.sample(time)
            input.apply(time)
            fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)
            time += step_size
        recorder.sample(time, force=True)
        fmu.terminate()
    except Exception as e:
        print("Simulation aborted. " + str(e))
    finally:
        fmu.freeInstance()

    return recorder.result()
