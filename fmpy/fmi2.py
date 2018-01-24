""" FMI 2.0 interface """

import pathlib
from ctypes import *
from . import free, calloc
from .fmi1 import _FMU, printLogMessage


fmi2Component            = c_void_p
fmi2ComponentEnvironment = c_void_p
fmi2FMUstate             = c_void_p
fmi2ValueReference       = c_uint
fmi2Real                 = c_double
fmi2Integer              = c_int
fmi2Boolean              = c_int
fmi2Char                 = c_char
fmi2String               = c_char_p
fmi2Type                 = c_int
fmi2Byte                 = c_char

fmi2Status  = c_int

fmi2OK      = 0
fmi2Warning = 1
fmi2Discard = 2
fmi2Error   = 3
fmi2Fatal   = 4
fmi2Pending = 5

fmi2CallbackLoggerTYPE         = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String)
fmi2CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi2CallbackFreeMemoryTYPE     = CFUNCTYPE(None, c_void_p)
fmi2StepFinishedTYPE           = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2Status)

fmi2ModelExchange = 0
fmi2CoSimulation  = 1

fmi2True  = 1
fmi2False = 0

fmi2StatusKind = c_int
fmi2DoStepStatus       = 0
fmi2PendingStatus      = 1
fmi2LastSuccessfulTime = 2
fmi2Terminated         = 3


def allocateMemory(nobj, size):
    return calloc(nobj, size)


def freeMemory(obj):
    free(obj)


def stepFinished(componentEnvironment, status):
    pass


class fmi2CallbackFunctions(Structure):

    _fields_ = [('logger',               fmi2CallbackLoggerTYPE),
                ('allocateMemory',       fmi2CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi2CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi2StepFinishedTYPE),
                ('componentEnvironment', fmi2ComponentEnvironment)]


class fmi2EventInfo(Structure):

    _fields_ = [('newDiscreteStatesNeeded',           fmi2Boolean),
                ('terminateSimulation',               fmi2Boolean),
                ('nominalsOfContinuousStatesChanged', fmi2Boolean),
                ('valuesOfContinuousStatesChanged',   fmi2Boolean),
                ('nextEventTimeDefined',              fmi2Boolean),
                ('nextEventTime',                     fmi2Real)]


class _FMU2(_FMU):
    """ Base class for FMI 2.0 FMUs """

    def __init__(self, **kwargs):

        super(_FMU2, self).__init__(**kwargs)

        # common FMI 2.0 functions
        self._fmi2Function('fmi2Instantiate',
                           ['instanceName', 'fmuType', 'guid', 'resourceLocation', 'callbacks', 'visible', 'loggingOn'],
                           [fmi2String, fmi2Type, fmi2String, fmi2String, POINTER(fmi2CallbackFunctions), fmi2Boolean,
                            fmi2Boolean],
                           fmi2Component)

        # Enter and exit initialization mode, terminate and reset
        self._fmi2Function('fmi2SetupExperiment',
                           ['component', 'toleranceDefined', 'tolerance', 'startTime', 'stopTimeDefined', 'stopTime'],
                           [fmi2Component, fmi2Boolean, fmi2Real, fmi2Real, fmi2Boolean, fmi2Real],
                           fmi2Status)

        self._fmi2Function('fmi2EnterInitializationMode', ['component'], [fmi2Component], fmi2Status)

        self._fmi2Function('fmi2ExitInitializationMode', ['component'], [fmi2Component], fmi2Status)

        self._fmi2Function('fmi2Terminate', ['component'], [fmi2Component], fmi2Status)

        self._fmi2Function('fmi2Reset', ['component'], [fmi2Component], fmi2Status)

        # Getting and setting variable values
        self._fmi2Function('fmi2GetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)],
                           fmi2Status)

        self._fmi2Function('fmi2GetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)],
                           fmi2Status)

        self._fmi2Function('fmi2GetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)],
                           fmi2Status)

        self._fmi2Function('fmi2GetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2String)],
                           fmi2Status)

        self._fmi2Function('fmi2SetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)],
                           fmi2Status)

        self._fmi2Function('fmi2SetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)],
                           fmi2Status)

        self._fmi2Function('fmi2SetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)],
                           fmi2Status)

        self._fmi2Function('fmi2SetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2String)],
                           fmi2Status)

        # Getting and setting the internal FMU state
        self._fmi2Function('fmi2GetFMUstate', ['component', 'state'], [fmi2Component, POINTER(fmi2FMUstate)], fmi2Status)

        self._fmi2Function('fmi2SetFMUstate', ['component', 'state'], [fmi2Component, fmi2FMUstate], fmi2Status)

        self._fmi2Function('fmi2FreeFMUstate', ['component', 'state'], [fmi2Component, POINTER(fmi2FMUstate)], fmi2Status)

        self._fmi2Function('fmi2FreeInstance', ['component'], [fmi2Component], None)

    def _fmi2Function(self, fname, argnames, argtypes, restype):

        if not hasattr(self.dll, fname):
            setattr(self, fname, None)
            return

        f = getattr(self.dll, fname)
        f.argtypes = argtypes
        f.restype = restype

        def w(*args, **kwargs):

            res = f(*args, **kwargs)

            if self.logFMICalls:
                self._print_fmi_args(fname, argnames, argtypes, args, restype, res)

            if restype == fmi2Status:  # status code
                # check the status code
                if res > 1:
                    raise Exception("FMI call failed with status %d." % res)

            return res

        setattr(self, fname, w)

    def instantiate(self, visible=False, callbacks=None, loggingOn=False):

        kind = fmi2ModelExchange if isinstance(self, FMU2Model) else fmi2CoSimulation
        resourceLocation = pathlib.Path(self.unzipDirectory, 'resources').as_uri()
        visible = fmi2True if visible else fmi2False

        if callbacks is None:
            callbacks = fmi2CallbackFunctions()
            callbacks.logger = fmi2CallbackLoggerTYPE(printLogMessage)
            callbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
            callbacks.freeMemory = fmi2CallbackFreeMemoryTYPE(freeMemory)

        self.callbacks = callbacks

        loggingOn = fmi2True if loggingOn else fmi2False

        self.component = self.fmi2Instantiate(self.instanceName.encode('utf-8'),
                                              kind,
                                              self.guid.encode('utf-8'),
                                              resourceLocation.encode('utf-8'),
                                              byref(self.callbacks),
                                              visible,
                                              loggingOn)

    def setupExperiment(self, tolerance=None, startTime=0.0, stopTime=None):

        toleranceDefined = fmi2True if tolerance is not None else fmi2False

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = fmi2True if stopTime is not None else fmi2False

        if stopTime is None:
            stopTime = 0.0

        return self.fmi2SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)

    def enterInitializationMode(self):
        return self.fmi2EnterInitializationMode(self.component)

    def exitInitializationMode(self):
        return self.fmi2ExitInitializationMode(self.component)

    def reset(self):
        return self.fmi2Reset(self.component)

    def terminate(self):
        return self.fmi2Terminate(self.component)

    def getReal(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))()
        self.fmi2GetReal(self.component, vr, len(vr), value)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Integer * len(vr))()
        self.fmi2GetInteger(self.component, vr, len(vr), value)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Boolean * len(vr))()
        self.fmi2GetBoolean(self.component, vr, len(vr), value)
        return list(value)

    def getString(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2String * len(vr))()
        self.fmi2GetString(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))(*value)
        self.fmi2SetReal(self.component, vr, len(vr), value)

    def setInteger(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Integer * len(vr))(*value)
        self.fmi2SetInteger(self.component, vr, len(vr), value)

    def setBoolean(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Boolean * len(vr))(*value)
        self.fmi2SetBoolean(self.component, vr, len(vr), value)

    def setString(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = map(lambda s: s.encode('utf-8'), value)
        value = (fmi2String * len(vr))(*value)
        self.fmi2SetString(self.component, vr, len(vr), value)

    def getFMUstate(self):
        state = fmi2FMUstate()
        self.fmi2GetFMUstate(self.component, byref(state))
        return state

    def setFMUstate(self, state):
        self.fmi2SetFMUstate(self.component, state)

    def freeFMUstate(self, state):
        self.fmi2FreeFMUstate(self.component, byref(state))

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)
        self.freeLibrary()


class FMU2Model(_FMU2):
    """ Base class for FMI 2.0 model exchange FMUs """

    def __init__(self, **kwargs):

        super(FMU2Model, self).__init__(**kwargs)

        self.eventInfo = fmi2EventInfo()

        self._fmi2Function('fmi2NewDiscreteStates',
                           ['component', 'eventInfo'],
                           [fmi2Component, POINTER(fmi2EventInfo)],
                           fmi2Status)

        self._fmi2Function('fmi2EnterContinuousTimeMode',
                           ['component'],
                           [fmi2Component],
                           fmi2Status)

        self._fmi2Function('fmi2EnterEventMode',
                           ['component'],
                           [fmi2Component],
                           fmi2Status)

        self._fmi2Function('fmi2GetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi2Component, POINTER(fmi2Real), c_size_t],
                           fmi2Status)

        self._fmi2Function('fmi2SetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi2Component, POINTER(fmi2Real), c_size_t],
                           fmi2Status)

        self._fmi2Function('fmi2GetDerivatives',
                           ['component', 'derivatives', 'nx'],
                           [fmi2Component, POINTER(fmi2Real), c_size_t],
                           fmi2Status)

        self._fmi2Function('fmi2GetEventIndicators',
                           ['component', 'eventIndicators', 'ni'],
                           [fmi2Component, POINTER(fmi2Real), c_size_t],
                           fmi2Status)

        self._fmi2Function('fmi2SetTime',
                           ['component', 'time'],
                           [fmi2Component, fmi2Real],
                           fmi2Status)

        self._fmi2Function('fmi2CompletedIntegratorStep',
                           ['component', 'noSetFMUStatePriorToCurrentPoint', 'enterEventMode', 'terminateSimulation'],
                           [fmi2Component, fmi2Boolean, POINTER(fmi2Boolean), POINTER(fmi2Boolean)],
                           fmi2Status)

    def newDiscreteStates(self):
        return self.fmi2NewDiscreteStates(self.component, byref(self.eventInfo))

    def enterContinuousTimeMode(self):
        return self.fmi2EnterContinuousTimeMode(self.component)

    def enterEventMode(self):
        return self.fmi2EnterEventMode(self.component)

    def getContinuousStates(self, x, nx):
        return self.fmi2GetContinuousStates(self.component, x, nx)

    def setContinuousStates(self, x, nx):
        return self.fmi2SetContinuousStates(self.component, x, nx)

    def getDerivatives(self, dx, nx):
        return self.fmi2GetDerivatives(self.component, dx, nx)

    def getEventIndicators(self, z, nz):
        return self.fmi2GetEventIndicators(self.component, z, nz)

    def setTime(self, time):
        return self.fmi2SetTime(self.component, time)

    def completedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint=fmi2True):
        enterEventMode = fmi2Boolean()
        terminateSimulation = fmi2Boolean()
        self.fmi2CompletedIntegratorStep(self.component, noSetFMUStatePriorToCurrentPoint, byref(enterEventMode), byref(terminateSimulation))
        return enterEventMode.value, terminateSimulation.value


class FMU2Slave(_FMU2):
    """ Base class for FMI 2.0 co-simulation FMUs """

    def __init__(self, instanceName=None, **kwargs):

        kwargs['instanceName'] = instanceName

        super(FMU2Slave, self).__init__(**kwargs)

        self._fmi2Function('fmi2SetRealInputDerivatives',
                           ['c', 'vr', 'nvr', 'order', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer), POINTER(fmi2Real)],
                           fmi2Status)

        self._fmi2Function('fmi2GetRealOutputDerivatives',
                           ['c', 'vr', 'nvr', 'order', 'value'],
                           [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer), POINTER(fmi2Real)],
                           fmi2Status)

        self._fmi2Function('fmi2DoStep',
                           ['component', 'currentCommunicationPoint', 'communicationStepSize',
                            'noSetFMUStatePriorToCurrentPoint'],
                           [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean],
                           fmi2Status)

        self._fmi2Function('fmi2GetBooleanStatus',
                           ['component', 'kind', 'value'],
                           [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)],
                           fmi2Status)

    def setRealInputDerivatives(self, vr, order, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        order = (fmi2Integer * len(vr))(*order)
        value = (fmi2Real * len(vr))(*value)
        self.fmi2SetRealInputDerivatives(self.component, vr, len(vr), order, value)

    def getRealOutputDerivatives(self, vr, order):
        vr = (fmi2ValueReference * len(vr))(*vr)
        order = (fmi2Integer * len(vr))(*order)
        value = (fmi2Real * len(vr))()
        self.fmi2GetRealOutputDerivatives(self.component, vr, len(vr), order, value)
        return list(value)

    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint=fmi2True):
        return self.fmi2DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        return self.fmi2GetBooleanStatus(self.component, kind, byref(value))
