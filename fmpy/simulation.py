# noinspection PyPep8

import shutil
import sys

from .fmi1 import *
from .fmi1 import _FMU1
from .fmi2 import *
from . import extract
from .util import auto_interval
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
        """ Record the variables """

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
        """ Return a structured NumPy array with the recorded results """

        return np.array(self.rows, dtype=np.dtype(self.cols))

    @property
    def lastSampleTime(self):
        """ Return the last sample time """

        if len(self.rows) > 0:
            return self.rows[-1][0]
        raise Exception("No samples available")


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

    def apply(self, time, continuous=True, discrete=True, after_event=False):

        if self.signals is None:
            return sys.float_info.max

        t = self.signals['time']

        # TODO: check for event

        if len(self.real_vrs) > 0 and continuous:
            self.real_values[:] = self.interpolate(time=time, t=t, table=self.real_table, after_event=after_event)
            self._setReal(self.fmu.component, self.real_vrs, len(self.real_vrs), self.real_values)

        # TODO: discrete apply Reals

        if len(self.integer_vrs) > 0 and discrete:
            self.integer_values[:] = self.interpolate(time=time, t=t, table=self.integer_table, discrete=True, after_event=after_event)
            self._setInteger(self.fmu.component, self.integer_vrs, len(self.integer_vrs), self.integer_values)

        if len(self.boolean_vrs) > 0 and discrete:
            self.boolean_values[:] = self.interpolate(time=time, t=t, table=self.boolean_table, discrete=True, after_event=after_event)
            self._setBoolean(self.fmu.component, self.boolean_vrs, len(self.boolean_vrs),
                             cast(self.boolean_values, POINTER(self._bool_type)))

        return Input.nextEvent(time, t)

    @staticmethod
    def nextEvent(time, t):

        i_events = np.argwhere(np.diff(t) == 0)
        t_events = t[i_events]

        i = np.argmax(t_events > time)

        if t_events[i] > time:
            return t_events[i][0]
        else:
            return sys.float_info.max

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


def apply_start_values(fmu, model_description, start_values, apply_default_start_values=False):
    """ Set start values to an FMU instance

    Parameters:
        fmu                     the FMU instance
        model_description       the ModelDescription instance
        start_values            dictionary of variable_name -> start_value pairs
        apply_default_values    apply the start values from the model description
    """

    start_values = start_values.copy()

    for variable in model_description.modelVariables:

        if variable.name in start_values:
            value = start_values.pop(variable.name)
        elif apply_default_start_values and variable.start is not None:
            value = variable.start
        else:
            continue

        vr = variable.valueReference

        if variable.type == 'Real':
            fmu.setReal([vr], [float(value)])
        elif variable.type in ['Integer', 'Enumeration']:
            fmu.setInteger([vr], [int(value)])
        elif variable.type == 'Boolean':
            if isinstance(value, str):
                if value.lower() not in ['true', 'false']:
                    raise Exception('The start value "%s" for variable "%s" could not be converted to Boolean' %
                                    (value, variable.name))
                else:
                    value = value.lower() == 'true'
            fmu.setBoolean([vr], [bool(value)])
        elif variable.type == 'String':
            fmu.setString([vr], [value])

    if len(start_values) > 0:
        raise Exception("The start values for the following variables could not be set because they don't exist: " +
                        ', '.join(start_values.keys()))


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
                 record_events=True,
                 fmi_type=None,
                 use_source_code=False,
                 start_values={},
                 apply_default_start_values=False,
                 input=None,
                 output=None,
                 timeout=None,
                 debug_logging=False,
                 logger=None,
                 fmi_call_logger=None,
                 step_finished=None,
                 model_description=None):
    """ Simulate an FMU

    Parameters:
        filename            filename of the FMU or directory with extracted FMU
        validate            validate the FMU
        start_time          simulation start time (None: use default experiment or 0 if not defined)
        stop_time           simulation stop time (None: use default experiment or start_time + 1 if not defined)
        solver              solver to use for model exchange ('Euler' or 'CVode')
        step_size           step size for the 'Euler' solver
        relative_tolerance  relative tolerance for the 'CVode' solver
        output_interval     interval for sampling the output
        record_events       record outputs at events (model exchange only)
        fmi_type            FMI type for the simulation (None: determine from FMU)
        use_source_code     compile the shared library (requires C sources)
        start_values        dictionary of variable name -> value pairs
        apply_default_start_values  apply the start values from the model description
        input               a structured numpy array that contains the input
        output              list of variables to record (None: record outputs)
        timeout             timeout for the simulation
        debug_logging       enable the FMU's debug logging
        fmi_call_logger     callback function to log FMI calls
        logger              callback function passed to the FMU (experimental)
        step_finished       callback to interact with the simulation (experimental)
        model_description   the previously loaded model description (experimental)

    Returns:
        result              a structured numpy array that contains the result
    """

    from fmpy import supported_platforms
    from fmpy.model_description import read_model_description

    if not use_source_code and platform not in supported_platforms(filename):
        raise Exception("The current platform (%s) is not supported by the FMU." % platform)

    if model_description is None:
        model_description = read_model_description(filename, validate=validate)
    else:
        model_description = model_description

    if fmi_type is None:
        # determine the FMI type automatically
        fmi_type = 'CoSimulation' if model_description.coSimulation is not None else 'ModelExchange'

    if fmi_type not in ['ModelExchange', 'CoSimulation']:
        raise Exception('fmi_type must be one of "ModelExchange" or "CoSimulation"')

    experiment = model_description.defaultExperiment

    if start_time is None:
        if experiment is not None and experiment.startTime is not None:
            start_time = experiment.startTime
        else:
            start_time = 0.0

    if stop_time is None:
        if experiment is not None and experiment.stopTime is not None:
            stop_time = experiment.stopTime
        else:
            stop_time = start_time + 1.0

    if relative_tolerance is None:
        if experiment is not None and experiment.tolerance is not None:
            relative_tolerance = experiment.tolerance
        else:
            relative_tolerance = 1e-5

    if step_size is None:
        total_time = stop_time - start_time
        step_size = 10 ** (np.round(np.log10(total_time)) - 3)

    if os.path.isfile(os.path.join(filename, 'modelDescription.xml')):
        unzipdir = filename
        tempdir = None
    else:
        tempdir = extract(filename)
        unzipdir = tempdir

    # common FMU constructor arguments
    fmu_args = {'guid': model_description.guid,
                'unzipDirectory': unzipdir,
                'instanceName': None,
                'fmiCallLogger': fmi_call_logger}

    if use_source_code:

        from .util import compile_dll

        # compile the shared library from the C sources
        fmu_args['libraryPath'] = compile_dll(model_description=model_description,
                                              sources_dir=os.path.join(unzipdir, 'sources'))

    if logger is None:
        logger = printLogMessage

    if model_description.fmiVersion == '1.0':
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
    if fmi_type == 'ModelExchange' and model_description.modelExchange is not None:
        fmu_args['modelIdentifier'] = model_description.modelExchange.modelIdentifier
        result = simulateME(model_description, fmu_args, start_time, stop_time, solver, step_size, relative_tolerance, start_values, apply_default_start_values, input, output, output_interval, record_events, timeout, callbacks, debug_logging, step_finished)
    elif fmi_type == 'CoSimulation' and model_description.coSimulation is not None:
        fmu_args['modelIdentifier'] = model_description.coSimulation.modelIdentifier
        result = simulateCS(model_description, fmu_args, start_time, stop_time, start_values, apply_default_start_values, input, output, output_interval, timeout, callbacks, debug_logging, step_finished)
    else:
        raise Exception('FMI type "%s" is not supported by the FMU' % fmi_type)

    # clean up
    if tempdir is not None:
        shutil.rmtree(tempdir)

    return result


def simulateME(model_description, fmu_kwargs, start_time, stop_time, solver_name, step_size, relative_tolerance, start_values, apply_default_start_values, input_signals, output, output_interval, record_events, timeout, callbacks, debug_logging, step_finished):

    if output_interval is None:
        if step_size is None:
            output_interval = auto_interval(stop_time - start_time)
        else:
            output_interval = step_size
            while (stop_time - start_time) / output_interval > 1000:
                output_interval *= 2

    if step_size is None:
        step_size = output_interval
        max_step = (stop_time - start_time) / 1000
        while step_size > max_step:
            step_size /= 2

    if not np.isclose(round(output_interval / step_size) * step_size, output_interval):
        raise Exception("output_interval must be a multiple of step_size")

    sim_start = current_time()

    # absolute tolerance for equality when comparing two floats
    eps = 1e-13

    time = start_time

    is_fmi1 = model_description.fmiVersion == '1.0'

    if is_fmi1:
        fmu = FMU1Model(**fmu_kwargs)
        fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        fmu.setTime(time)
    else:
        fmu = FMU2Model(**fmu_kwargs)
        fmu.instantiate(callbacks=callbacks, loggingOn=debug_logging)
        fmu.setupExperiment(startTime=start_time)

    # set the start values
    apply_start_values(fmu, model_description, start_values, apply_default_start_values)

    input = Input(fmu, model_description, input_signals)
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
        'nx': model_description.numberOfContinuousStates,
        'nz': model_description.numberOfEventIndicators,
        'get_x': fmu.getContinuousStates,
        'set_x': fmu.setContinuousStates,
        'get_dx': fmu.getDerivatives,
        'get_z': fmu.getEventIndicators
    }

    # select the solver
    if solver_name == 'Euler':
        solver = ForwardEuler(**solver_args)
        fixed_step = True
    elif solver_name is None or solver_name == 'CVode':
        from .sundials import CVodeSolver
        solver = CVodeSolver(set_time=fmu.setTime,
                             startTime=start_time,
                             maxStep=(stop_time - start_time) / 50.,
                             relativeTolerance=relative_tolerance,
                             **solver_args)
        step_size = output_interval
        fixed_step = False
    else:
        raise Exception("Unknown solver: %s. Must be one of 'Euler' or 'CVode'." % solver_name)

    recorder = Recorder(fmu=fmu,
                        modelDescription=model_description,
                        variableNames=output,
                        interval=output_interval)

    # record the values for time == start_time
    recorder.sample(time)

    t_next = start_time

    # simulation loop
    while time < stop_time:

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

        if fixed_step:
            if time + step_size < stop_time + eps:
                t_next = time + step_size
            else:
                break
        else:
            if time + eps >= t_next:  # t_next has been reached
                # integrate to the next grid point
                t_next = round(time / output_interval) * output_interval + output_interval

        t_input_event = input.apply(time)

        # check for input event
        input_event = t_input_event <= t_next

        if input_event:
            t_next = t_input_event

        if is_fmi1:
            time_event = fmu.eventInfo.upcomingTimeEvent != fmi1False and fmu.eventInfo.nextEventTime <= t_next
        else:
            time_event = fmu.eventInfo.nextEventTimeDefined != fmi2False and fmu.eventInfo.nextEventTime <= t_next

        if time_event and not fixed_step:
            t_next = fmu.eventInfo.nextEventTime

        if t_next - time > eps:
            # do one step
            state_event, time = solver.step(time, t_next)
        else:
            # skip
            time = t_next

        # set the time
        fmu.setTime(time)

        # check for step event, e.g.dynamic state selection
        if is_fmi1:
            step_event = fmu.completedIntegratorStep()
        else:
            step_event, _ = fmu.completedIntegratorStep()
            step_event = step_event != fmi2False

        # handle events
        if input_event or time_event or state_event or step_event:

            if record_events:
                # record the values before the event
                recorder.sample(time, force=True)

            if input_event:
                input.apply(time=time, after_event=True)

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

            if record_events:
                # record values after the event
                recorder.sample(time, force=True)

        if abs(time - round(time / output_interval) * output_interval) < eps and time != recorder.lastSampleTime:
            # record values for this step
            recorder.sample(time, force=True)

        if step_finished is not None and not step_finished(time, recorder):
            break

    fmu.terminate()

    fmu.freeInstance()

    del solver

    return recorder.result()


def simulateCS(model_description, fmu_kwargs, start_time, stop_time, start_values, apply_default_start_values, input_signals, output, output_interval, timeout, callbacks, debug_logging, step_finished):

    if output_interval is None:
        output_interval = auto_interval(stop_time - start_time)

    sim_start = current_time()

    if model_description.fmiVersion == '1.0':
        fmu = FMU1Slave(**fmu_kwargs)
        fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        apply_start_values(fmu, model_description, start_values, apply_default_start_values)
        fmu.initialize()
    else:
        fmu = FMU2Slave(**fmu_kwargs)
        fmu.instantiate(callbacks=callbacks, loggingOn=debug_logging)
        fmu.setupExperiment(tolerance=None, startTime=start_time)
        apply_start_values(fmu, model_description, start_values, apply_default_start_values)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    input = Input(fmu=fmu, modelDescription=model_description, signals=input_signals)

    recorder = Recorder(fmu=fmu,
                        modelDescription=model_description,
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
