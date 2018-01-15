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
    """ Helper class to record the variables during the simulation """

    def __init__(self, fmu, modelDescription, variableNames=None, interval=None):
        """
        Parameters:
            fmu               the FMU instance
            modelDescription  the model description instance
            variableNames     list of variable names to record
            interval          minimum distance to the previous sample
        """

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

        self.constants = {}
        self.modelDescription = modelDescription

        # collect the variables to record
        for sv in modelDescription.modelVariables:

            # collect the variables to record
            if (variableNames is not None and sv.name in variableNames) or (variableNames is None and sv.causality == 'output'):

                if sv.type == 'Real':
                    real_names.append(sv.name)
                    self.real_vrs.append(sv.valueReference)
                elif sv.type in ['Integer', 'Enumeration']:
                    integer_names.append(sv.name)
                    self.integer_vrs.append(sv.valueReference)
                elif sv.type == 'Boolean':
                    boolean_names.append(sv.name)
                    self.boolean_vrs.append(sv.valueReference)
                else:
                    pass  # skip String variables

        self.cols += zip(real_names, [np.float64] * len(real_names))
        self.cols += zip(integer_names, [np.int32] * len(integer_names))
        self.cols += zip(boolean_names, [np.bool_] * len(boolean_names))

    def sample(self, time, force=False):

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
    """ Helper class that sets the input to the FMU """

    def __init__(self, fmu, modelDescription, signals):
        """
        Parameters:
            fmu               the FMU instance
            modelDescription  the model description instance
            signals           a structured numpy array that contains the input
        """

        self.fmu = fmu
        self.signals = signals

        if signals is None:
            return

        is_fmi1 = isinstance(fmu, _FMU1)

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
    """ Set start values to an FMU instance

    Parameters:
        fmu               the FMU instance
        modelDescription  the ModelDescription instance
        start_values      dictionary of variable_name -> value pairs
    """

    variables = {}

    for v in modelDescription.modelVariables:
        variables[v.name] = v

    for name, value in start_values.items():

        if name not in variables:
            raise Exception("The variable '%s' could not be set because it does not exist in the FMU." % name)

        v = variables[name]
        vr = v.valueReference

        if v.type == 'Real':
            value = float(value)
            fmu.setReal([vr], [value])
        elif v.type in ['Integer', 'Enumeration']:
            value = int(value)
            fmu.setInteger([vr], [value])
        elif v.type == 'Boolean':
            value = bool(value)
            fmu.setBoolean([vr], [value])
        elif v.type == 'String':
            fmu.setString([vr], [value])


class ForwardEuler(object):

    def __init__(self, nx, nz, get_x, set_x, get_dx, get_z):

        self.get_x = get_x
        self.set_x = set_x
        self.get_dx = get_dx
        self.get_z = get_z

        self.x = np.zeros(nx)
        self.dx = np.zeros(nx)
        self.z = np.zeros(nz)
        self.prez = np.zeros(nz)

        self._px = self.x.ctypes.data_as(POINTER(c_double))
        self._pdx = self.dx.ctypes.data_as(POINTER(c_double))
        self._pz = self.z.ctypes.data_as(POINTER(c_double))
        self._pprez = self.z.ctypes.data_as(POINTER(c_double))

        # initialize the event indicators
        self.get_z(self._pz, self.z.size)

    def step(self, t, tNext):

        # get the current states and derivatives
        self.get_x(self._px, self.x.size)
        self.get_dx(self._pdx, self.dx.size)

        # perform one step
        dt = tNext - t
        self.x += dt * self.dx

        # set the continuous states
        self.set_x(self._px, self.x.size)

        # check for state event
        self.prez[:] = self.z
        self.get_z(self._pz, self.z.size)
        stateEvent = np.any((self.prez * self.z) < 0)

        return stateEvent, tNext

    def reset(self, time):
        pass  # nothing to do


def simulate_fmu(filename,
                 validate=True,
                 start_time=None,
                 stop_time=None,
                 solver='CVode',
                 step_size=None,
                 relative_tolerance=None,
                 output_interval=None,
                 fmi_type=None,
                 use_source_code=False,
                 start_values={},
                 input=None,
                 output=None,
                 timeout=None,
                 fmi_logging=False,
                 logger=None,
                 step_finished=None):
    """ Simulate an FMU

    Parameters:
        filename            filename of the FMU
        validate            validate the FMU
        start_time          simulation start time (None: use default experiment or 0 if not defined)
        stop_time           simulation stop time (None: use default experiment or start_time + 1 if not defined)
        solver              solver to use for model exchange ('Euler' or 'CVode')
        step_size           step size for the 'Euler' solver
        relative_tolerance  relative tolerance for the 'CVode' solver
        output_interval     interval for sampling the output
        fmi_type            FMI type for the simulation (None: determine from FMU)
        use_source_code     compile the shared library (requires C sources)
        start_values        dictionary of variable name -> value pairs
        input               a structured numpy array that contains the input
        output              list of variables to record (None: record outputs)
        timeout             timeout for the simulation
        fmi_logging         whether to log FMI calls
        logger              callback function passed to the FMU (experimental)
        step_finished       callback to interact with the simulation (experimental)

    Returns:
        result              a structured numpy array that contains the result
    """

    modelDescription = read_model_description(filename, validate=validate)

    if fmi_type is None:
        # determine the FMI type automatically
        fmi_type = 'CoSimulation' if modelDescription.coSimulation is not None else 'ModelExchange'

    if fmi_type not in ['ModelExchange', 'CoSimulation']:
        raise Exception('fmi_type must be one of "ModelExchange" or "CoSimulation"')

    defaultExperiment = modelDescription.defaultExperiment

    if start_time is None:
        if defaultExperiment is not None and defaultExperiment.startTime is not None:
            start_time = defaultExperiment.startTime
        else:
            start_time = 0.0

    if stop_time is None:
        if defaultExperiment is not None and defaultExperiment.stopTime is not None:
            stop_time = defaultExperiment.stopTime
        else:
            stop_time = start_time + 1.0

    if relative_tolerance is None:
        if defaultExperiment is not None and defaultExperiment.tolerance is not None:
            relative_tolerance = defaultExperiment.tolerance
        else:
            relative_tolerance = 1e-5

    if step_size is None:
        total_time = stop_time - start_time
        step_size = 10 ** (np.round(np.log10(total_time)) - 3)

    # extract the FMU
    unzipdir = extract(filename)

    # common FMU constructor arguments
    fmu_args = {'guid': modelDescription.guid,
                'unzipDirectory': unzipdir,
                'instanceName': None,
                'logFMICalls': fmi_logging}

    if use_source_code:

        from .util import compile_dll

        # compile the shared library from the C sources
        fmu_args['libraryPath'] = compile_dll(model_description=modelDescription,
                                              sources_dir=os.path.join(unzipdir, 'sources'))

    if output_interval is None:
        output_interval = (stop_time - start_time) / 500

    if logger is None:
        logger = printLogMessage

    if modelDescription.fmiVersion == '1.0':
        callbacks = fmi1CallbackFunctions()
        callbacks.logger = fmi1CallbackLoggerTYPE(logger)
        callbacks.allocateMemory = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
        callbacks.freeMemory = fmi1CallbackFreeMemoryTYPE(freeMemory)
        callbacks.stepFinished = None
    else:
        callbacks = fmi2CallbackFunctions()
        callbacks.logger = fmi2CallbackLoggerTYPE(logger)
        callbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
        callbacks.freeMemory = fmi2CallbackFreeMemoryTYPE(freeMemory)

    # simulate_fmu the FMU
    if fmi_type == 'ModelExchange':
        fmu_args['modelIdentifier'] = modelDescription.modelExchange.modelIdentifier
        result = simulateME(modelDescription, fmu_args, start_time, stop_time, solver, step_size, relative_tolerance, start_values, input, output, output_interval, timeout, callbacks, step_finished)
    elif fmi_type == 'CoSimulation':
        fmu_args['modelIdentifier'] = modelDescription.coSimulation.modelIdentifier
        result = simulateCS(modelDescription, fmu_args, start_time, stop_time, start_values, input, output, output_interval, timeout, callbacks, step_finished)

    # clean up
    shutil.rmtree(unzipdir)

    return result


def simulateME(modelDescription, fmu_kwargs, start_time, stop_time, solver_name, step_size, relative_tolerance, start_values, input_signals, output, output_interval, timeout, callbacks, step_finished):

    sim_start = current_time()

    time = start_time

    is_fmi1 = modelDescription.fmiVersion == '1.0'

    if is_fmi1:
        fmu = FMU1Model(**fmu_kwargs)
        fmu.instantiate(functions=callbacks)
        fmu.setTime(time)
    else:
        fmu = FMU2Model(**fmu_kwargs)
        fmu.instantiate(callbacks=callbacks)
        fmu.setupExperiment(startTime=start_time)

    # set the start values
    apply_start_values(fmu, modelDescription, start_values)

    input = Input(fmu, modelDescription, input_signals)
    input.apply(time)

    if is_fmi1:
        fmu.initialize()
    else:
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        # event iteration
        fmu.eventInfo.newDiscreteStatesNeeded = fmi2True
        fmu.eventInfo.terminateSimulation = fmi2False

        while fmu.eventInfo.newDiscreteStatesNeeded == fmi2True and fmu.eventInfo.terminateSimulation == fmi2False:
            # update discrete states
            fmu.newDiscreteStates()

        fmu.enterContinuousTimeMode()

    # common solver constructor arguments
    solver_args = {
        'nx': modelDescription.numberOfContinuousStates,
        'nz': modelDescription.numberOfEventIndicators,
        'get_x': fmu.getContinuousStates,
        'set_x': fmu.setContinuousStates,
        'get_dx': fmu.getDerivatives,
        'get_z': fmu.getEventIndicators
    }

    # select the solver
    if solver_name == 'Euler':
        solver = ForwardEuler(**solver_args)
    elif solver_name is None or solver_name == 'CVode':
        from .sundials import CVodeSolver
        solver = CVodeSolver(set_time=fmu.setTime,
                             startTime=start_time,
                             maxStep=(stop_time - start_time) / 50.,
                             relativeTolerance=relative_tolerance,
                             **solver_args)
        step_size = output_interval
    else:
        raise Exception("Unknown solver: %s. Must be one of 'Euler' or 'CVode'." % solver_name)

    recorder = Recorder(fmu=fmu,
                        modelDescription=modelDescription,
                        variableNames=output,
                        interval=output_interval)

    # simulation loop
    while time < stop_time:

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

        input.apply(time)

        tNext = min(time + step_size, stop_time)

        if is_fmi1:
            timeEvent = fmu.eventInfo.upcomingTimeEvent != fmi1False and fmu.eventInfo.nextEventTime <= time
        else:
            timeEvent = fmu.eventInfo.nextEventTimeDefined != fmi2False and fmu.eventInfo.nextEventTime <= time

        if timeEvent:
            tNext = fmu.eventInfo.nextEventTime

        if tNext - time > 1e-13:
            # perform one step
            stateEvent, time = solver.step(time, tNext)
        else:
            # skip
            time = tNext

        # set the time
        fmu.setTime(time)

        # check for step event, e.g.dynamic state selection
        if is_fmi1:
            stepEvent = fmu.completedIntegratorStep()
        else:
            stepEvent, terminateSimulation = fmu.completedIntegratorStep()
            stepEvent = stepEvent != fmi2False

        # record the values for this step
        recorder.sample(time)

        # handle events
        if timeEvent or stateEvent or stepEvent:

            if is_fmi1:
                fmu.eventUpdate()
            else:
                # handle events
                fmu.enterEventMode()

                fmu.eventInfo.newDiscreteStatesNeeded = fmi2True
                fmu.eventInfo.terminateSimulation = fmi2False

                # update discrete states
                while fmu.eventInfo.newDiscreteStatesNeeded != fmi2False and fmu.eventInfo.terminateSimulation == fmi2False:
                    fmu.newDiscreteStates()

                fmu.enterContinuousTimeMode()

            solver.reset(time)
            # record values after the event
            recorder.sample(time)

        if step_finished is not None and not step_finished(time, recorder):
            break

    recorder.sample(time, force=True)

    fmu.terminate()

    fmu.freeInstance()

    del solver

    return recorder.result()


def simulateCS(modelDescription, fmu_kwargs, start_time, stop_time, start_values, input_signals, output, output_interval, timeout, callbacks, step_finished):

    sim_start = current_time()

    if modelDescription.fmiVersion == '1.0':
        fmu = FMU1Slave(**fmu_kwargs)
        fmu.instantiate("instance1", functions=callbacks)
        apply_start_values(fmu, modelDescription, start_values)
        fmu.initialize()
    else:
        fmu = FMU2Slave(**fmu_kwargs)
        fmu.instantiate(callbacks=callbacks)
        fmu.setupExperiment(tolerance=None, startTime=start_time)
        apply_start_values(fmu, modelDescription, start_values)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    input = Input(fmu=fmu, modelDescription=modelDescription, signals=input_signals)

    recorder = Recorder(fmu=fmu,
                        modelDescription=modelDescription,
                        variableNames=output,
                        interval=output_interval)

    time = start_time

    # simulation loop
    while time < stop_time:

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

        recorder.sample(time)

        input.apply(time)

        fmu.doStep(currentCommunicationPoint=time, communicationStepSize=output_interval)

        if step_finished is not None and not step_finished(time, recorder):
            break

        time += output_interval

    recorder.sample(time, force=True)

    fmu.terminate()

    fmu.freeInstance()

    return recorder.result()
