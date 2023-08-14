# noinspection PyPep8

import shutil

from fmpy.model_description import ModelDescription

from .fmi1 import *
from .fmi1 import _FMU1, _FMU
from .fmi2 import *
from .fmi2 import _FMU2
from . import fmi3
from . import extract
from .util import auto_interval, add_remoting
import numpy as np
from time import time as current_time
from typing import Union, Any, Dict, Sequence, Callable

# absolute tolerance for equality when comparing two floats
eps = 1e-13


class SimulationResult(np.ndarray):

    def __new__(subtype, shape, dtype=float, buffer=None, offset=0, strides=None, order=None, modelDescription=None):
        obj = super(SimulationResult, subtype).__new__(subtype, shape, dtype, buffer, offset, strides, order)
        obj.modelDescription = modelDescription
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.modelDescription = getattr(obj, 'modelDescription', None)


def _get_output_variables(model_description, max_variables=5):
    """ Create a list of default output variables """

    output_variables = []

    # output variables
    for variable in model_description.modelVariables:
        if variable.causality == 'output':
            output_variables.append(variable)

    if len(output_variables) > 0:
        return output_variables

    # continuous states
    if model_description.derivatives is not None:
        output_variables = [derivative.variable.derivative for derivative in model_description.derivatives]

    if len(output_variables) > 0:
        return output_variables[:max_variables]

    # local variables
    for variable in model_description.modelVariables:
        if variable.variability == 'local':
            output_variables.append(variable)

    if len(output_variables) > 0:
        return output_variables[:max_variables]

    # any variable
    return model_description.modelVariables[:max_variables]


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

        self.cols = [('time', np.float64, None)]  # name, dtype, shape
        self.rows = []
        self.info = {}  # type -> (names, vrs, shapes, n_values, getter)
        self.types = []

        self.constants = {}
        self.modelDescription = modelDescription

        if variableNames is None:
            variableNames = [variable.name for variable in _get_output_variables(modelDescription)]

        # collect the variables to record
        for sv in modelDescription.modelVariables:

            if sv.name == 'time':
                continue  # "time" is reserved for the simulation time

            # collect the variables to record
            if sv.name in variableNames:
                type = sv.type
                if type == 'Enumeration':
                    type = 'Integer' if modelDescription.fmiVersion in {'1.0', '2.0'} else 'Int64'
                names, vrs, shapes, n_values, getter = self.info.get(type, ([], [], [], 0, getattr(self.fmu, 'get' + type)))
                names.append(sv.name)
                vrs.append(sv.valueReference)
                shapes.append(sv.shape)
                n_values += np.prod(sv.shape) if sv.shape else 1
                self.info[type] = names, vrs, shapes, n_values, getter

        # create the columns for the NumPy array
        if modelDescription.fmiVersion in ['1.0', '2.0']:
            types = [('Real', np.float64), ('Integer', np.int32), ('Boolean', np.bool_)]
        else:
            types = [
                ('Float32', np.float32),
                ('Float64', np.float64),
                ('Int8', np.int8),
                ('UInt8', np.uint8),
                ('Int16', np.int16),
                ('UInt16', np.uint16),
                ('Int32', np.int32),
                ('UInt32', np.uint32),
                ('Int64', np.int64),
                ('UInt64', np.uint64),
                ('Boolean', np.bool_),
            ]

        # collect the columns
        for t, dt in types:
            if t in self.info:
                self.types.append(t)
                names, _, shapes, _, _ = self.info[t]
                self.cols += zip(names, [dt] * len(names), shapes)

        # strip the shape for scalars
        self.cols = [(n, t) if not s else (n, t, s) for n, t, s in self.cols]

    @staticmethod
    def _append_reshaped(row, values, shapes):
        i = 0
        for d in shapes:
            if d:
                s = np.prod(d)
                value = np.array(values[i:i + s]).reshape(d)
                i += s
            else:
                value = values[i]
                i += 1
            row.append(value)

    def sample(self, time, force=False):
        """ Record the variables """

        if not force and self.interval is not None and len(self.rows) > 0:
            last = self.rows[-1][0]
            if time - last + eps < self.interval:
                return

        row = [time]

        for t in self.types:
            names, vrs, shapes, nValues, getter = self.info[t]
            if self.modelDescription.fmiVersion in ['1.0', '2.0']:
                values = getter(vr=vrs)
            else:
                values = getter(vr=vrs, nValues=nValues)
            self._append_reshaped(row, values, shapes)

        self.rows.append(tuple(row))

    def result(self):
        """ Return a structured NumPy array with the recorded results """

        arr = np.array(self.rows, dtype=np.dtype(self.cols))

        info_arr = arr.view(SimulationResult)

        info_arr.modelDescription = self.modelDescription

        return info_arr

    @property
    def lastSampleTime(self):
        """ Return the last sample time """

        if len(self.rows) > 0:
            return self.rows[-1][0]
        raise Exception("No samples available")


class Input(object):
    """ Helper class that sets the input to the FMU """

    def __init__(self, fmu, modelDescription, signals, set_input_derivatives=False):
        """
        Parameters:
            fmu                    the FMU instance
            modelDescription       the model description instance
            signals                a structured numpy array that contains the input
            set_input_derivatives  calculate and set the input derivatives

        Example:

        Create a Real signal 'step' and a Boolean signal 'switch' with a discrete step at t=0.5

        >>> import numpy as np
        >>> dtype = [('time', np.double), ('step', np.double), ('switch', np.bool_)]
        >>> signals = np.array([(0.0, 0.0, False), (0.5, 0.0, False), (0.5, 0.1, True), (1.0, 1.0, True)], dtype=dtype)
        """

        self.fmu = fmu

        if signals is None:
            self.t = None
            return

        # get the time grid
        self.t = signals[signals.dtype.names[0]]

        # find events
        self.t_events = Input.findEvents(signals, modelDescription)

        self.set_input_derivatives = set_input_derivatives

        is_fmi1 = isinstance(fmu, _FMU1)
        is_fmi2 = isinstance(fmu, _FMU2)

        setters = dict()

        # get the setters
        if is_fmi1:
            setters['Real']        = (fmu.fmi1SetReal,    fmi1Real)
            setters['Integer']     = (fmu.fmi1SetInteger, fmi1Integer)
            setters['Boolean']     = (fmu.fmi1SetBoolean, c_int8)
            setters['Enumeration'] = (fmu.fmi1SetInteger, fmi1Integer)
        elif is_fmi2:
            setters['Real']        = (fmu.fmi2SetReal,    fmi2Real)
            setters['Integer']     = (fmu.fmi2SetInteger, fmi2Integer)
            setters['Boolean']     = (fmu.fmi2SetBoolean, fmi2Boolean)
            setters['Enumeration'] = (fmu.fmi2SetInteger, fmi2Integer)
        else:
            setters['Float32']     = (fmu.fmi3SetFloat32, fmi3.fmi3Float32)
            setters['Float64']     = (fmu.fmi3SetFloat64, fmi3.fmi3Float64)
            setters['Int8']        = (fmu.fmi3SetInt8,    fmi3.fmi3Int8)
            setters['UInt8']       = (fmu.fmi3SetUInt8,   fmi3.fmi3UInt8)
            setters['Int16']       = (fmu.fmi3SetInt16,   fmi3.fmi3Int16)
            setters['UInt16']      = (fmu.fmi3SetUInt16,  fmi3.fmi3UInt16)
            setters['Int32']       = (fmu.fmi3SetInt32,   fmi3.fmi3Int32)
            setters['UInt32']      = (fmu.fmi3SetUInt32,  fmi3.fmi3UInt32)
            setters['Int64']       = (fmu.fmi3SetInt64,   fmi3.fmi3Int64)
            setters['UInt64']      = (fmu.fmi3SetUInt64,  fmi3.fmi3UInt64)
            setters['Boolean']     = (fmu.fmi3SetBoolean, fmi3.fmi3Boolean)
            setters['Enumeration'] = (fmu.fmi3SetInt64,   fmi3.fmi3Int64)

        from collections import defaultdict

        continuous_inputs = defaultdict(list)
        discrete_inputs = defaultdict(list)

        self.continuous = []
        self.discrete = []

        for variable in modelDescription.modelVariables:

            if variable.causality != 'input' and variable.variability != 'tunable':
                continue

            if variable.name not in signals.dtype.names:
                if variable.causality == 'input':
                    print('Warning: missing input for variable "%s"' % variable.name)
                continue

            if variable.type in {'Float32', 'Float64', 'Real'} and variable.variability not in ['discrete', 'tunable']:
                continuous_inputs[variable.type].append((variable.valueReference, variable.name))
            else:
                discrete_inputs[variable.type].append((variable.valueReference, variable.name))

        for type_, vrs_and_names in continuous_inputs.items():
            vrs, names = zip(*vrs_and_names)
            setter, value_type = setters[type_]
            self.continuous.append((
                (c_uint32 * len(vrs))(*vrs),
                (value_type * len(vrs))(),
                (c_int * len(vrs))(*([1] * len(vrs))),
                (value_type * len(vrs))(),
                np.asarray(np.stack(list(map(lambda n: signals[n], names))), dtype=value_type),
                setter
            ))

        for type_, vrs_and_names in discrete_inputs.items():
            vrs, names = zip(*vrs_and_names)
            setter, value_type = setters[type_]
            self.discrete.append((
                (c_uint32 * len(vrs))(*vrs),
                (value_type * len(vrs))(),
                np.asarray(np.stack(list(map(lambda n: signals[n], names))), dtype=value_type),
                setter
            ))

    def apply(self, time, continuous=True, discrete=True, after_event=False):
        """ Apply the input

        Parameters:
            continuous   apply continuous inputs
            discrete     apply discrete inputs
            after_event  apply right hand side inputs at discontinuities
        """

        if self.t is None:
            return

        is_fmi1 = isinstance(self.fmu, _FMU1)
        is_fmi3 = isinstance(self.fmu, fmi3._FMU3)

        # continuous
        if continuous:
            for vrs, values, order, derivatives, table, setter in self.continuous:
                values[:], derivatives[:] = self.interpolate(time=time, t=self.t, table=table, discrete=False, after_event=after_event)
                if is_fmi3:
                    setter(self.fmu.component, vrs, len(vrs), values, len(values))
                else:
                    setter(self.fmu.component, vrs, len(vrs), values)

                if self.set_input_derivatives:
                    self.fmu.fmi2SetRealInputDerivatives(self.fmu.component, vrs, len(vrs), order, derivatives)

        # discrete
        if discrete:
            for vrs, values, table, setter in self.discrete:
                values[:], der_values = self.interpolate(time=time, t=self.t, table=table, discrete=True, after_event=after_event)

                if is_fmi1 and values._type_ == c_int8:
                    # special treatment for fmi1Boolean
                    setter(self.fmu.component, vrs, len(vrs), cast(values, POINTER(c_char)))
                else:
                    if is_fmi3:
                        setter(self.fmu.component, vrs, len(vrs), values, len(values))
                    else:
                        setter(self.fmu.component, vrs, len(vrs), values)

    def nextEvent(self, time):
        """ Get the next input event """

        if self.t is None:
            return float('Inf')

        # find the next event
        i = np.argmax(self.t_events > time)
        return self.t_events[i]

    @staticmethod
    def findEvents(signals, model_description):
        """ Find time events """

        t_event = {float('Inf')}

        if signals.size < 2:
            return np.array(list(t_event))  # only one sample

        t = signals[signals.dtype.names[0]]

        # continuous
        i_event = np.where(np.diff(t) == 0)
        t_event.update(t[i_event])

        # discrete
        for variable in model_description.modelVariables:
            if variable.name in signals.dtype.names and variable.variability in ['discrete', 'tunable']:
                y = signals[variable.name]
                i_event = np.flatnonzero(np.diff(y))
                t_event.update(t[i_event + 1])

        return np.array(sorted(t_event))

    @staticmethod
    def interpolate(time, t, table, discrete=False, after_event=False):

        if t.size < 2:
            return table, np.zeros_like(table)  # only one sample

        # find the left insert index
        i0 = np.searchsorted(t, time)

        if i0 == 0:
            values = table[:, 0]  # hold first value
            return values, np.zeros_like(values)

        if i0 == len(t):
            values = table[:, -1]  # hold last value
            return values, np.zeros_like(values)

        # check for event
        if time == t[i0] and i0 < len(t) - 1 and t[i0] == t[i0 + 1]:

            der_v = np.zeros((table.shape[0],))

            if after_event:
                # take the value after the event
                while i0 < len(t) - 1 and t[i0] == t[i0 + 1]:
                    i0 += 1
                if i0 < len(t) - 1:
                    v0 = table[:, i0]
                    v1 = table[:, i0 + 1]
                    t0 = t[i0]
                    t1 = t[i0 + 1]
                    if not discrete:
                        der_v = (v1 - v0) / (t1 - t0)
            else:
                v0 = table[:, i0 - 1]
                v1 = table[:, i0]
                t0 = t[i0 - 1]
                t1 = t[i0]
                if not discrete:
                    der_v = (v1 - v0) / (t1 - t0)

            values = table[:, i0]
            return values, der_v

        i0 -= 1  # interpolate
        i1 = i0 + 1

        if discrete:
            values = table[:, i1 if after_event else i0]
            return values, np.zeros_like(values)

        t0 = t[i0]
        t1 = t[i1]

        w0 = (t1 - time) / (t1 - t0)
        w1 = 1 - w0

        v0 = table[:, i0]
        v1 = table[:, i1]

        # interpolate the input value
        v = w0 * v0 + w1 * v1
        der_v = (v1 - v0) / (t1 - t0)

        return v, der_v


def apply_start_values(fmu, model_description, start_values, settable=None):
    """ Set start values to an FMU instance

    Parameters:
        fmu                the FMU instance
        model_description  the ModelDescription instance
        start_values       dictionary of variable_name -> start_value pairs
        settable           callback f(variable) -> bool that indicates if a variable can be set

    returns:
        a dictionary with the start values that have not been set
    """

    start_values = start_values.copy()

    unit_definitions = dict((u.name, dict((d.name, d) for d in u.displayUnits)) for u in model_description.unitDefinitions)

    for variable in model_description.modelVariables:

        if variable.name not in start_values:
            continue

        if settable is not None and not settable(variable):
            continue

        value = start_values.pop(variable.name)

        if type(value) is tuple:
            if len(value) != 2:
                raise Exception(f'The start value for variable {variable.name} must be a scalar value or a'
                                f' tuple (<value>, {{<unit>|<display_unit>}}) but was "{value}".')
            value, unit = value
        else:
            unit = None

        if unit is None or unit == variable.unit:
            pass
        elif variable.declaredType is not None and unit == variable.declaredType.unit:
            pass
        else:
            if variable.unit is not None:
                base_unit = variable.unit
            elif variable.declaredType is not None:
                base_unit = variable.declaredType.unit
            else:
                raise Exception(f'Variable {variable.name} has no unit but the unit "{unit}"'
                                ' was specified for its start value.')

            if unit not in unit_definitions[base_unit]:
                raise Exception(f'The unit "{unit}" of the start value for variable {variable.name} is not defined.')

            display_unit = unit_definitions[base_unit][unit]
            value = (value - display_unit.offset) / display_unit.factor

        vr = variable.valueReference

        # get the setter function
        if variable.type == 'Enumeration':
            if model_description.fmiVersion in {'1.0', '2.0'}:
                setter = getattr(fmu, 'setInteger')
            else:
                setter = getattr(fmu, 'setInt64')
        else:
            setter = getattr(fmu, 'set' + variable.type)

        # convert Boolean values
        if variable.type == 'Boolean':
            if isinstance(value, str):
                if value.lower() not in ['true', 'false']:
                    raise Exception(f'The start value "{value}" for variable "{variable.name}"'
                                    ' could not be converted to Boolean')
                else:
                    value = value.lower() == 'true'

        # convert the type
        if variable.shape:
            if isinstance(value, str):
                value = value.split()
            value = list(map(lambda e: variable._python_type(e), value))
            if len(value) != np.prod(variable.shape):
                raise ArgumentError(f'The start value for variable "{variable.name}" must have'
                                    f' {np.prod(variable.shape)} elements but has {len(value)}.')
        else:
            value = [variable._python_type(value)]

        setter([vr], value)

    return start_values


class ForwardEuler(object):

    def __init__(self, nx, nz, get_x, set_x, get_dx, get_z, input):

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

        roots = np.zeros_like(self.z, dtype=np.int32)

        # find zero crossings
        for i, (prez, z) in enumerate(zip(self.prez, self.z)):
            if prez < 0 and z >= 0:
                roots[i] = -1
            elif prez > 0 and z <= 0:
                roots[i] = 1

        return np.any(roots != 0), roots, tNext

    def reset(self, time):
        pass  # nothing to do


def simulate_fmu(filename,
                 validate: bool = True,
                 start_time: Union[float, str] = None,
                 stop_time: Union[float, str] = None,
                 solver: str = 'CVode',
                 step_size: Union[float, str] = None,
                 relative_tolerance: Union[float, str] = None,
                 output_interval: Union[float, str] = None,
                 record_events: bool = True,
                 fmi_type: str = None,
                 start_values: Dict[str, Any] = {},
                 apply_default_start_values: bool = False,
                 input: np.ndarray = None,
                 output: Sequence[str] = None,
                 timeout: Union[float, str] = None,
                 debug_logging: bool = False,
                 visible: bool = False,
                 logger: Callable = None,
                 fmi_call_logger: Callable[[str], None] = None,
                 step_finished: Callable[[float, Recorder], bool] = None,
                 model_description: ModelDescription = None,
                 fmu_instance: _FMU = None,
                 set_input_derivatives: bool = False,
                 remote_platform: str = 'auto',
                 early_return_allowed: bool = False,
                 use_event_mode: bool = False,
                 initialize: bool = True,
                 terminate: bool = True,
                 fmu_state: Union[bytes, c_void_p] = None,
                 set_stop_time: bool = True) -> SimulationResult:
    """ Simulate an FMU

    Parameters:
        filename               filename of the FMU or directory with extracted FMU
        validate               validate the FMU and start values
        start_time             simulation start time (None: use default experiment or 0 if not defined)
        stop_time              simulation stop time (None: use default experiment or start_time + 1 if not defined)
        solver                 solver to use for model exchange ('Euler' or 'CVode')
        step_size              step size for the 'Euler' solver
        relative_tolerance     relative tolerance for the 'CVode' solver and FMI 2.0 co-simulation FMUs
        output_interval        interval for sampling the output
        record_events          record outputs at events (model exchange only)
        fmi_type               FMI type for the simulation (None: determine from FMU)
        start_values           dictionary of variable name -> value pairs
        apply_default_start_values  apply the start values from the model description (deprecated)
        input                  a structured numpy array that contains the input (see :class:`Input`)
        output                 list of variables to record (None: record outputs)
        timeout                timeout for the simulation
        debug_logging          enable the FMU's debug logging
        visible                interactive mode (True) or batch mode (False)
        fmi_call_logger        callback function to log FMI calls
        logger                 callback function passed to the FMU (experimental)
        step_finished          callback to interact with the simulation (experimental)
        model_description      the previously loaded model description (experimental)
        fmu_instance           the previously instantiated FMU (experimental)
        set_input_derivatives  set the input derivatives (FMI 2.0 Co-Simulation only)
        remote_platform        platform to use for remoting server ('auto': determine automatically if current platform
                               is not supported, None: no remoting; experimental)
        early_return_allowed   allow early return in FMI 3.0 Co-Simulation
        use_event_mode         use event mode in FMI 3.0 Co-Simulation if the FMU supports it
        initialize             initialize the FMU
        terminate              terminate the FMU
        fmu_state              the FMU state or serialized FMU state to initialize the FMU
        set_stop_time          communicate the stop time to the FMU instance
    Returns:
        result                 a structured numpy array that contains the result
    """

    from fmpy import supported_platforms
    from fmpy.model_description import read_model_description
    from fmpy.util import can_simulate

    platforms = supported_platforms(filename)

    if fmu_instance is None and platform not in platforms and remote_platform is None:
        raise Exception(f"The current platform ({platform}) is not supported by the FMU.")

    can_sim, remote_platform = can_simulate(platforms, remote_platform)

    if not can_sim:
        raise Exception(f"The FMU cannot be simulated on the current platform ({platform}).")

    if model_description is None:
        model_description = read_model_description(filename, validate=validate)

    if fmi_type is None:
        if fmu_instance is not None:
            # determine FMI type from the FMU instance
            fmi_type = 'CoSimulation' if type(fmu_instance) in [FMU1Slave, FMU2Slave, fmi3.FMU3Slave] else 'ModelExchange'
        else:
            # determine the FMI type automatically
            fmi_type = 'CoSimulation' if model_description.coSimulation is not None else 'ModelExchange'

    if fmi_type not in ['ModelExchange', 'CoSimulation']:
        raise Exception('fmi_type must be one of "ModelExchange" or "CoSimulation"')

    if initialize is False:
        if fmi_type != 'CoSimulation':
            raise Exception("If initialize is False, the interface type must be 'CoSimulation'.")
        if fmu_instance is None and fmu_state is None:
            raise Exception("If initialize is False, fmu_instance or fmu_state must be provided.")

    experiment = model_description.defaultExperiment

    if start_time is None:
        if experiment is not None and experiment.startTime is not None:
            start_time = experiment.startTime
        else:
            start_time = 0.0

    start_time = float(start_time)

    if stop_time is None:
        if experiment is not None and experiment.stopTime is not None:
            stop_time = experiment.stopTime
        else:
            stop_time = start_time + 1.0

    stop_time = float(stop_time)

    if relative_tolerance is None and experiment is not None:
        relative_tolerance = experiment.tolerance

    if step_size is None:
        total_time = stop_time - start_time
        step_size = 10 ** (np.round(np.log10(total_time)) - 3)

    if output_interval is None and fmi_type == 'CoSimulation':

        co_simulation = model_description.coSimulation

        if co_simulation is not None and co_simulation.fixedInternalStepSize is not None:
            output_interval = float(model_description.coSimulation.fixedInternalStepSize)
        elif experiment is not None and experiment.stepSize is not None:
            output_interval = float(experiment.stepSize)

        if output_interval is not None:
            while (stop_time - start_time) / output_interval > 1000:
                output_interval *= 2

    if os.path.isfile(os.path.join(filename, 'modelDescription.xml')):
        unzipdir = filename
        tempdir = None
    else:
        required_paths = ['resources', 'binaries/']
        if remote_platform:
            required_paths.append(os.path.join('binaries', remote_platform))
        tempdir = extract(filename, include=None if remote_platform else lambda n: n.startswith(tuple(required_paths)))
        unzipdir = tempdir

    if remote_platform:
        add_remoting(unzipdir, host_platform=platform, remote_platform=remote_platform)

    if fmu_instance is None:
        fmu = instantiate_fmu(unzipdir, model_description, fmi_type, visible, debug_logging, logger, fmi_call_logger, None, early_return_allowed, use_event_mode, None, validate)
    else:
        fmu = fmu_instance

    if fmu_state is not None:
        if model_description.fmiVersion == '2.0' or model_description.fmiVersion.startswith('3.0'):
            if isinstance(fmu_state, bytes):
                fmu_state = fmu.deserializeFMUState(fmu_state)
                fmu.setFMUState(fmu_state)
                fmu.freeFMUState(fmu_state)
            else:
                fmu.setFMUState(fmu_state)
        else:
            raise Exception(f"Setting the FMU state is not supported for FMI version {model_description.fmiVersion}.")
        initialize = False

    # simulate_fmu the FMU
    if fmi_type == 'ModelExchange':
        result = simulateME(model_description, fmu, start_time, stop_time, solver, step_size, relative_tolerance, start_values, apply_default_start_values, input, output, output_interval, record_events, timeout, step_finished, validate, set_stop_time)
    elif fmi_type == 'CoSimulation':
        result = simulateCS(model_description, fmu, start_time, stop_time, relative_tolerance, start_values, apply_default_start_values, input, output, output_interval, timeout, step_finished, set_input_derivatives, use_event_mode, early_return_allowed, validate, initialize, terminate, set_stop_time)

    if fmu_instance is None:
        fmu.freeInstance()

    # clean up
    if tempdir is not None:
        shutil.rmtree(tempdir, ignore_errors=True)

    return result


def instantiate_fmu(unzipdir, model_description, fmi_type=None, visible=False, debug_logging=False, logger=None, fmi_call_logger=None, library_path=None, early_return_allowed=False, event_mode_used=False, intermediate_update=None, require_functions=True):
    """
    Create an instance of fmpy.fmi1._FMU (see simulate_fmu() for documentation of the parameters).
    """

    # common constructor arguments
    fmu_args = {
        'guid': model_description.guid,
        'unzipDirectory': unzipdir,
        'instanceName': None,
        'fmiCallLogger': fmi_call_logger,
        'requireFunctions': require_functions
    }

    if library_path:
        fmu_args['libraryPath'] = library_path

    is_fmi1 = model_description.fmiVersion == '1.0'
    is_fmi2 = model_description.fmiVersion == '2.0'

    if logger is not None and (is_fmi1 or is_fmi2):

        if is_fmi1:
            callbacks = fmi1CallbackFunctions()
            callbacks.logger         = fmi1CallbackLoggerTYPE(logger)
            callbacks.allocateMemory = fmi1CallbackAllocateMemoryTYPE(calloc)
            callbacks.freeMemory     = fmi1CallbackFreeMemoryTYPE(free)
            callbacks.stepFinished   = None
        else:
            callbacks = fmi2CallbackFunctions()
            callbacks.logger         = fmi2CallbackLoggerTYPE(logger)
            callbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(calloc)
            callbacks.freeMemory     = fmi2CallbackFreeMemoryTYPE(free)

        try:
            from .logging import addLoggerProxy
            addLoggerProxy(byref(callbacks))
        except Exception as e:
            print(f"Failed to add logger proxy function. {e}")
    else:
        callbacks = None

    if fmi_type in [None, 'CoSimulation'] and model_description.coSimulation is not None:

        fmu_args['modelIdentifier'] = model_description.coSimulation.modelIdentifier

        if is_fmi1:
            fmu = FMU1Slave(**fmu_args)
            fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        elif is_fmi2:
            fmu = FMU2Slave(**fmu_args)
            fmu.instantiate(visible=visible, callbacks=callbacks, loggingOn=debug_logging)
        else:
            fmu = fmi3.FMU3Slave(**fmu_args)
            fmu.instantiate(visible=visible, loggingOn=debug_logging, eventModeUsed=event_mode_used,
                            earlyReturnAllowed=early_return_allowed, logMessage=logger,
                            intermediateUpdate=intermediate_update)

    elif fmi_type in [None, 'ModelExchange'] and model_description.modelExchange is not None:

        fmu_args['modelIdentifier'] = model_description.modelExchange.modelIdentifier

        if is_fmi1:
            fmu = FMU1Model(**fmu_args)
            fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        elif is_fmi2:
            fmu = FMU2Model(**fmu_args)
            fmu.instantiate(visible=visible, callbacks=callbacks, loggingOn=debug_logging)
        else:
            fmu = fmi3.FMU3Model(**fmu_args)
            fmu.instantiate(visible=visible, loggingOn=debug_logging, logMessage=logger)

    elif fmi_type in [None, 'ScheduledExecution'] and model_description.scheduledExecution is not None:

        fmu_args['modelIdentifier'] = model_description.scheduledExecution.modelIdentifier
        fmu = fmi3.FMU3ScheduledExecution(**fmu_args)
        fmu.instantiate(visible=visible, loggingOn=debug_logging, logMessage=logger)

    else:

        raise Exception('FMI type "%s" is not supported by the FMU' % fmi_type)

    return fmu


def has_start_value(variable):
    return variable.start is not None


def settable_in_instantiated(variable):
    return variable.causality == 'input' \
           or variable.variability != 'constant' and variable.initial in {'approx', 'exact'}


def settable_in_initialization_mode(variable):
    return variable.causality == 'input' \
           or (variable.causality != 'parameter' and variable.variability == 'tunable') \
           or (variable.variability != 'constant' and variable.initial == 'exact')


def simulateME(model_description, fmu, start_time, stop_time, solver_name, step_size, relative_tolerance, start_values, apply_default_start_values, input_signals, output, output_interval, record_events, timeout, step_finished, validate, set_stop_time):

    if relative_tolerance is None:
        relative_tolerance = 1e-5

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

    sim_start = current_time()

    time = start_time

    is_fmi1 = model_description.fmiVersion == '1.0'
    is_fmi2 = model_description.fmiVersion == '2.0'
    is_fmi3 = model_description.fmiVersion.startswith('3.0')

    if is_fmi1:
        fmu.setTime(time)
    elif is_fmi2:
        fmu.setupExperiment(startTime=start_time, stopTime=stop_time if set_stop_time else None)

    input = Input(fmu, model_description, input_signals)

    # initialize
    if is_fmi1:
        start_values = apply_start_values(fmu, model_description, start_values, settable=has_start_value)

        input.apply(time)

        (iterationConverged,
         stateValueReferencesChanged,
         stateValuesChanged,
         terminate_simulation,
         nextEventTimeDefined,
         nextEventTime) = fmu.initialize()

        if terminate_simulation:
            raise Exception('Model requested termination during initial event update.')

    elif is_fmi2:

        start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)

        fmu.enterInitializationMode()

        start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_initialization_mode)

        input.apply(time)

        fmu.exitInitializationMode()

        newDiscreteStatesNeeded = True
        terminate_simulation = False

        while newDiscreteStatesNeeded and not terminate_simulation:
            (newDiscreteStatesNeeded,
             terminate_simulation,
             nominalsOfContinuousStatesChanged,
             valuesOfContinuousStatesChanged,
             nextEventTimeDefined,
             nextEventTime) = fmu.newDiscreteStates()

        if terminate_simulation:
            raise Exception('Model requested termination during initial event update.')

        fmu.enterContinuousTimeMode()

    elif is_fmi3:

        start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)

        fmu.enterInitializationMode(startTime=start_time, stopTime=stop_time if set_stop_time else None)

        input.apply(time)

        start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_initialization_mode)

        fmu.exitInitializationMode()

        discreteStatesNeedUpdate = True
        terminate_simulation = False

        while discreteStatesNeedUpdate and not terminate_simulation:
            # update discrete states
            (discreteStatesNeedUpdate,
             terminate_simulation,
             nominalsOfContinuousStatesChanged,
             valuesOfContinuousStatesChanged,
             nextEventTimeDefined,
             nextEventTime) = fmu.updateDiscreteStates()

        fmu.enterContinuousTimeMode()

    if validate and len(start_values) > 0:
        raise Exception("The start values for the following variables could not be set: " +
                        ', '.join(start_values.keys()))

    # common solver constructor arguments
    solver_args = {
        'nx': model_description.numberOfContinuousStates,
        'nz': model_description.numberOfEventIndicators,
        'get_x': fmu.getContinuousStates,
        'set_x': fmu.setContinuousStates,
        'get_dx': fmu.getContinuousStateDerivatives if is_fmi3 else fmu.getDerivatives,
        'get_z': fmu.getEventIndicators,
        'input': input
    }

    # select the solver
    if solver_name == 'Euler':
        solver = ForwardEuler(**solver_args)
        fixed_step = True
    elif solver_name is None or solver_name == 'CVode':
        from .sundials import CVodeSolver
        solver = CVodeSolver(get_nominals=fmu.getNominalContinuousStates if is_fmi1 else fmu.getNominalsOfContinuousStates,
                             set_time=fmu.setTime,
                             startTime=start_time,
                             maxStep=(stop_time - start_time) / 50.,
                             relativeTolerance=relative_tolerance,
                             **solver_args)
        step_size = output_interval
        fixed_step = False
    else:
        raise Exception("Unknown solver: %s. Must be one of 'Euler' or 'CVode'." % solver_name)

    # check step size
    if fixed_step and not np.isclose(round(output_interval / step_size) * step_size, output_interval):
        raise Exception("output_interval must be a multiple of step_size for fixed step solvers")

    recorder = Recorder(fmu=fmu,
                        modelDescription=model_description,
                        variableNames=output,
                        interval=output_interval)

    # record the values for time == start_time
    recorder.sample(time)

    t_next = start_time

    n_fixed_steps = 0

    # simulation loop
    while time < stop_time:

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

        if fixed_step:
            t_next = start_time + n_fixed_steps * step_size
            if t_next > stop_time:
                break
            n_fixed_steps += 1
        else:
            if time + eps >= t_next:  # t_next has been reached
                # integrate to the next grid point
                t_next = np.floor(time / output_interval) * output_interval + output_interval
                if t_next < time + eps:
                    t_next += output_interval

        # get the next input event
        t_input_event = input.nextEvent(time)

        # check for input event
        input_event = t_input_event <= t_next

        if input_event:
            t_next = t_input_event

        time_event = nextEventTimeDefined and nextEventTime <= t_next

        if time_event and not fixed_step:
            t_next = nextEventTime

        if t_next - time > eps:
            # do one step
            state_event, roots_found, time = solver.step(time, t_next)
        else:
            # skip
            state_event = False
            roots_found = []
            time = t_next

        # set the time
        fmu.setTime(time)

        # apply continuous inputs
        input.apply(time, discrete=False)

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

            if is_fmi1:

                if input_event:
                    input.apply(time=time, after_event=True)

                iterationConverged = False

                # update discrete states
                while not iterationConverged and not terminate_simulation:
                    (iterationConverged,
                     stateValueReferencesChanged,
                     stateValuesChanged,
                     terminate_simulation,
                     nextEventTimeDefined,
                     nextEventTime) = fmu.eventUpdate()

                if terminate_simulation:
                    break

            elif is_fmi2:

                fmu.enterEventMode()

                if input_event:
                    input.apply(time=time, after_event=True)

                newDiscreteStatesNeeded = True

                # update discrete states
                while newDiscreteStatesNeeded and not terminate_simulation:
                    (newDiscreteStatesNeeded,
                     terminate_simulation,
                     nominalsOfContinuousStatesChanged,
                     valuesOfContinuousStatesChanged,
                     nextEventTimeDefined,
                     nextEventTime) = fmu.newDiscreteStates()

                if terminate_simulation:
                    break

                fmu.enterContinuousTimeMode()

            else:

                fmu.enterEventMode()

                if input_event:
                    input.apply(time=time, after_event=True)

                newDiscreteStatesNeeded = True

                # update discrete states
                while newDiscreteStatesNeeded and not terminate_simulation:
                    (newDiscreteStatesNeeded,
                     terminate_simulation,
                     nominalsOfContinuousStatesChanged,
                     valuesOfContinuousStatesChanged,
                     nextEventTimeDefined,
                     nextEventTime) = fmu.updateDiscreteStates()

                if terminate_simulation:
                    break

                fmu.enterContinuousTimeMode()

            solver.reset(time)

            if record_events:
                # record values after the event
                recorder.sample(time, force=True)

        if abs(time - round(time / output_interval) * output_interval) < eps and time > recorder.lastSampleTime + eps:
            # record values for this step
            recorder.sample(time, force=True)

        if step_finished is not None and not step_finished(time, recorder):
            break

    fmu.terminate()

    del solver

    return recorder.result()


def simulateCS(model_description, fmu, start_time, stop_time, relative_tolerance, start_values, apply_default_start_values, input_signals, output, output_interval, timeout, step_finished, set_input_derivatives, use_event_mode, early_return_allowed, validate, initialize, terminate, set_stop_time):

    if set_input_derivatives and not model_description.coSimulation.canInterpolateInputs:
        raise Exception("Parameter set_input_derivatives is True but the FMU cannot interpolate inputs.")

    if output_interval is None:
        output_interval = auto_interval(stop_time - start_time)

    sim_start = current_time()

    is_fmi1 = model_description.fmiVersion == '1.0'
    is_fmi2 = model_description.fmiVersion == '2.0'

    input = Input(fmu=fmu, modelDescription=model_description, signals=input_signals, set_input_derivatives=set_input_derivatives)

    time = start_time

    if initialize:

        # initialize the model
        if is_fmi1:
            start_values = apply_start_values(fmu, model_description, start_values, settable=has_start_value)
            input.apply(time)
            fmu.initialize(tStart=time, stopTime=stop_time if set_stop_time else None)
        elif is_fmi2:
            fmu.setupExperiment(tolerance=relative_tolerance, startTime=time, stopTime=stop_time if set_stop_time else None)
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)
            fmu.enterInitializationMode()
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_initialization_mode)
            input.apply(time)
            fmu.exitInitializationMode()
        else:
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_instantiated)
            fmu.enterInitializationMode(tolerance=relative_tolerance, startTime=time, stopTime=stop_time if set_stop_time else None)
            start_values = apply_start_values(fmu, model_description, start_values, settable=settable_in_initialization_mode)
            input.apply(time)
            fmu.exitInitializationMode()

            if use_event_mode:

                update_discrete_states = True

                while update_discrete_states:
                    update_discrete_states, terminate_simulation, _, _, _, _ = fmu.updateDiscreteStates()

                if terminate_simulation:
                    raise Exception("The FMU requested to terminate the simulation during initialization.")

                fmu.enterStepMode()

    if validate and len(start_values) > 0:
        raise Exception("The start values for the following variables could not be set: " +
                        ', '.join(start_values.keys()))

    recorder = Recorder(fmu=fmu, modelDescription=model_description, variableNames=output, interval=output_interval)

    n_steps = time / output_interval

    terminate_simulation = False

    # simulation loop
    while True:

        recorder.sample(time, force=True)

        if timeout is not None and (current_time() - sim_start) > timeout:
            break

        if terminate_simulation or time >= stop_time:
            break

        input.apply(time)

        if is_fmi1:

            if time + output_interval <= stop_time:
                fmu.doStep(currentCommunicationPoint=time, communicationStepSize=output_interval)
                n_steps += 1
                time = n_steps * output_interval
            else:
                fmu.doStep(currentCommunicationPoint=time, communicationStepSize=stop_time - time)
                time = stop_time

        elif is_fmi2:

            try:
                if time + output_interval <= stop_time:
                    fmu.doStep(currentCommunicationPoint=time, communicationStepSize=output_interval)
                    n_steps += 1
                    time = n_steps * output_interval
                else:
                    fmu.doStep(currentCommunicationPoint=time, communicationStepSize=stop_time - time)
                    time = stop_time
            except FMICallException as e:
                if e.status == fmi2Discard:
                    terminated = fmu.getBooleanStatus(fmi2Terminated)
                    if terminated:
                        time = fmu.getRealStatus(fmi2LastSuccessfulTime)
                        recorder.sample(time, force=True)
                        break
                else:
                    raise e
        else:

            t_input_event = input.nextEvent(time)

            t_next = (n_steps + 1) * output_interval

            input_event = t_next > t_input_event

            step_size = t_input_event - time if input_event else t_next - time

            event_encountered, terminate_simulation, early_return, last_successful_time = fmu.doStep(currentCommunicationPoint=time, communicationStepSize=step_size)

            if early_return and not early_return_allowed:
                raise Exception("FMU returned early from doStep() but Early Return is not allowed.")

            if early_return and last_successful_time < t_next:
                time = last_successful_time
            else:
                time = t_next
                n_steps += 1

            if use_event_mode and (input_event or event_encountered):

                recorder.sample(last_successful_time, force=True)

                fmu.enterEventMode()

                input.apply(last_successful_time, after_event=True)

                update_discrete_states = True

                while update_discrete_states and not terminate_simulation:
                    update_discrete_states, terminate_simulation, _, _, _, _ = fmu.updateDiscreteStates()

                if terminate_simulation:
                    break

                fmu.enterStepMode()

        if step_finished is not None and not step_finished(time, recorder):
            recorder.sample(time, force=True)
            break

    if terminate:
        fmu.terminate()

    return recorder.result()
