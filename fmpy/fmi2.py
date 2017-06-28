# noinspection PyPep8

from ctypes import *
from itertools import combinations
from . import free, freeLibrary, calloc, CO_SIMULATION, MODEL_EXCHANGE
from .fmi1 import _FMU
import numpy as np


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

fmi2Status = c_int

fmi2OK      = 0
fmi2Warning = 1
fmi2Discard = 2
fmi2Error   = 3
fmi2Fatal   = 4
fmi2Pending = 5

fmi2CallbackLoggerTYPE         = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String, fmi2String)
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


def fmi2Call(func):

    def func_wrapper(self, *args, **kwargs):

        status = func(self, *args, **kwargs)

        if status not in [fmi2OK, fmi2Warning]:
            # TODO: terminate FMU
            # TODO: log this
            values = list(args)
            values += map(lambda it: "%s=%s" % (it[0], it[1]), kwargs.items())
            raise Exception("FMI call %s(%s) returned status %d" % (func.__name__, ', '.join(values), status))

        return status

    return func_wrapper


def logger(componentEnvironment, instanceName, status, category, message, va_list):
    print(componentEnvironment, instanceName, status, category, message, va_list)


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

callbacks = fmi2CallbackFunctions()
callbacks.logger               = fmi2CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
#callbacks.stepFinished         = fmi2StepFinishedTYPE(stepFinished)
callbacks.freeMemory           = fmi2CallbackFreeMemoryTYPE(freeMemory)
#callbacks.componentEnvironment = None

class fmi2EventInfo(Structure):
    _fields_ = [('newDiscreteStatesNeeded',           fmi2Boolean),
                ('terminateSimulation',               fmi2Boolean),
                ('nominalsOfContinuousStatesChanged', fmi2Boolean),
                ('valuesOfContinuousStatesChanged',   fmi2Boolean),
                ('nextEventTimeDefined',              fmi2Boolean),
                ('nextEventTime',                     fmi2Real)]


variables = {}


class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None
        self.type = None
        self.start = None
        self.causality = None
        self.variability = None


class _FMU2(_FMU):

    def __init__(self, modelDescription, unzipDirectory, instanceName, fmiType):

        super(_FMU2, self).__init__(modelDescription, unzipDirectory, instanceName, fmiType)

        # common FMI 2.0 functions
        self.fmi2Instantiate = getattr(self.dll, 'fmi2Instantiate')
        self.fmi2Instantiate.argtypes = [fmi2String, fmi2Type, fmi2String, fmi2String, POINTER(fmi2CallbackFunctions), fmi2Boolean, fmi2Boolean]
        self.fmi2Instantiate.restype = fmi2ComponentEnvironment

        self.fmi2SetupExperiment          = getattr(self.dll, 'fmi2SetupExperiment')
        self.fmi2SetupExperiment.argtypes = [fmi2Component, fmi2Boolean, fmi2Real, fmi2Real, fmi2Boolean, fmi2Real]
        self.fmi2SetupExperiment.restype  = fmi2Status

        self.fmi2EnterInitializationMode          = getattr(self.dll, 'fmi2EnterInitializationMode')
        self.fmi2EnterInitializationMode.argtypes = [fmi2Component]
        self.fmi2EnterInitializationMode.restype  = fmi2Status

        self.fmi2ExitInitializationMode          = getattr(self.dll, 'fmi2ExitInitializationMode')
        self.fmi2ExitInitializationMode.argtypes = [fmi2Component]
        self.fmi2ExitInitializationMode.restype  = fmi2Status

        self.fmi2GetReal          = getattr(self.dll, 'fmi2GetReal')
        self.fmi2GetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2GetReal.restype  = fmi2Status

        self.fmi2GetInteger          = getattr(self.dll, 'fmi2GetInteger')
        self.fmi2GetInteger.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)]
        self.fmi2GetInteger.restype  = fmi2Status

        self.fmi2GetBoolean          = getattr(self.dll, 'fmi2GetBoolean')
        self.fmi2GetBoolean.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)]
        self.fmi2GetBoolean.restype  = fmi2Status

        self.fmi2GetString           = getattr(self.dll, 'fmi2GetString')
        self.fmi2GetString.argtypes  = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2String)]
        self.fmi2GetString.restype   = fmi2Status

        self.fmi2SetReal          = getattr(self.dll, 'fmi2SetReal')
        self.fmi2SetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2SetReal.restype  = fmi2Status

        self.fmi2SetInteger          = getattr(self.dll, 'fmi2SetInteger')
        self.fmi2SetInteger.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)]
        self.fmi2SetInteger.restype  = fmi2Status

        self.fmi2SetBoolean          = getattr(self.dll, 'fmi2SetBoolean')
        self.fmi2SetBoolean.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)]
        self.fmi2SetBoolean.restype  = fmi2Status

        self.fmi2SetString           = getattr(self.dll, 'fmi2SetString')
        self.fmi2SetString.argtypes  = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2String)]
        self.fmi2SetString.restype   = fmi2Status

        self.fmi2Terminate          = getattr(self.dll, 'fmi2Terminate')
        self.fmi2Terminate.argtypes = [fmi2Component]
        self.fmi2Terminate.restype  = fmi2Status

        self.fmi2FreeInstance          = getattr(self.dll, 'fmi2FreeInstance')
        self.fmi2FreeInstance.argtypes = [fmi2Component]
        self.fmi2FreeInstance.restype  = None


    def assertNoError(self, status):
        if status not in [fmi2OK, fmi2Warning]:
            raise Exception("FMI call failed")

    def instantiate(self):

        kind = fmi2ModelExchange if self.fmiType == MODEL_EXCHANGE else fmi2CoSimulation

        self.component = self.fmi2Instantiate(self.instanceName.encode('utf-8'),
                                              kind,
                                              self.modelDescription.guid.encode('utf-8'),
                                              self.fmuLocation.encode('utf-8'),
                                              byref(callbacks), fmi2False,
                                              fmi2False)

    # @fmiCall
    def setupExperiment(self, tolerance, startTime, stopTime=None):

        toleranceDefined = tolerance is not None

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = stopTime is not None

        if stopTime is None:
            stopTime = 0.0

        status = self.fmi2SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined,
                                          stopTime)
        return status

    def enterInitializationMode(self):
        status = self.fmi2EnterInitializationMode(self.component)
        self.assertNoError(status)
        return status

    def exitInitializationMode(self):
        status = self.fmi2ExitInitializationMode(self.component)
        self.assertNoError(status)
        return status

    def getReal(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))()
        status = self.fmi2GetReal(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Integer * len(vr))()
        status = self.fmi2GetInteger(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Boolean * len(vr))()
        status = self.fmi2GetBoolean(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def getString(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2String * len(vr))()
        status = self.fmi2GetString(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))(*value)
        status = self.fmi2SetReal(self.component, vr, len(vr), value)
        self.assertNoError(status)

    def setInteger(self, vr, value):
        value = map(lambda s: s.encode('utf-8'), value)
        value = (fmi2String * len(vr))(*value)
        status = self.fmi2SetString(self.component, vr, len(vr), value)
        self.assertNoError(status)

    def terminate(self):
        status = self.fmi2Terminate(self.component)
        self.assertNoError(status)

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)

        # unload the shared library
        freeLibrary(self.dll._handle)


class FMU2Model(_FMU2):

    def __init__(self, modelDescription, unzipDirectory, instanceName=None):

        super(FMU2Model, self).__init__(modelDescription, unzipDirectory, instanceName, MODEL_EXCHANGE)

        self.eventInfo = fmi2EventInfo()

        nx = modelDescription.numberOfContinuousStates
        nz = modelDescription.numberOfEventIndicators

        self.x  = np.zeros(nx)
        self.dx = np.zeros(nx)
        self.z  = np.zeros(nz)

        self._px  = self.x.ctypes.data_as(POINTER(fmi2Real))
        self._pdx = self.dx.ctypes.data_as(POINTER(fmi2Real))
        self._pz  = self.z.ctypes.data_as(POINTER(fmi2Real))

        self.fmi2NewDiscreteStates = getattr(self.dll, 'fmi2NewDiscreteStates')
        self.fmi2NewDiscreteStates.argtypes = [fmi2Component, POINTER(fmi2EventInfo)]
        self.fmi2NewDiscreteStates.restype = fmi2Status

        self.fmi2EnterContinuousTimeMode = getattr(self.dll, 'fmi2EnterContinuousTimeMode')
        self.fmi2EnterContinuousTimeMode.argtypes = [fmi2Component]
        self.fmi2EnterContinuousTimeMode.restype = fmi2Status

        self.fmi2EnterEventMode = getattr(self.dll, 'fmi2EnterEventMode')
        self.fmi2EnterEventMode.argtypes = [fmi2Component]
        self.fmi2EnterEventMode.restype = fmi2Status

        self.fmi2GetContinuousStates = getattr(self.dll, 'fmi2GetContinuousStates')
        self.fmi2GetContinuousStates.argtypes = [fmi2Component, POINTER(fmi2Real), c_size_t]
        self.fmi2GetContinuousStates.restype = fmi2Status

        self.fmi2SetContinuousStates = getattr(self.dll, 'fmi2SetContinuousStates')
        self.fmi2SetContinuousStates.argtypes = [fmi2Component, POINTER(fmi2Real), c_size_t]
        self.fmi2SetContinuousStates.restype = fmi2Status

        self.fmi2GetDerivatives = getattr(self.dll, 'fmi2GetDerivatives')
        self.fmi2GetDerivatives.argtypes = [fmi2Component, POINTER(fmi2Real), c_size_t]
        self.fmi2GetDerivatives.restype = fmi2Status

        self.fmi2GetEventIndicators = getattr(self.dll, 'fmi2GetEventIndicators')
        self.fmi2GetEventIndicators.argtypes = [fmi2Component, POINTER(fmi2Real), c_size_t]
        self.fmi2GetEventIndicators.restype = fmi2Status

        self.fmi2SetTime = getattr(self.dll, 'fmi2SetTime')
        self.fmi2SetTime.argtypes = [fmi2Component, fmi2Real]
        self.fmi2SetTime.restype = fmi2Status

        self.fmi2CompletedIntegratorStep = getattr(self.dll, 'fmi2CompletedIntegratorStep')
        self.fmi2CompletedIntegratorStep.argtypes = [fmi2Component, fmi2Boolean, POINTER(fmi2Boolean), POINTER(fmi2Boolean)]
        self.fmi2CompletedIntegratorStep.restype = fmi2Status

    @fmi2Call
    def newDiscreteStates(self):
        return self.fmi2NewDiscreteStates(self.component, byref(self.eventInfo))

    @fmi2Call
    def enterContinuousTimeMode(self):
        return self.fmi2EnterContinuousTimeMode(self.component)

    @fmi2Call
    def enterEventMode(self):
        return self.fmi2EnterEventMode(self.component)

    @fmi2Call
    def getContinuousStates(self):
        return self.fmi2GetContinuousStates(self.component, self._px, self.x.size)
        # TODO: check status

    def setContinuousStates(self):
        status = self.fmi2SetContinuousStates(self.component, self._px, self.x.size)
        # TODO: check status

    def getDerivatives(self):
        status = self.fmi2GetDerivatives(self.component, self._pdx, self.dx.size)
        # TODO: check status

    def getEventIndicators(self):
        status = self.fmi2GetEventIndicators(self.component, self._pz, self.z.size)
        # TODO: check status

    def setTime(self, time):
        status = self.fmi2SetTime(self.component, time)
        # TODO: check status

    def completedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint=fmi2True):
        enterEventMode = fmi2Boolean()
        terminateSimulation = fmi2Boolean()
        status = self.fmi2CompletedIntegratorStep(self.component, noSetFMUStatePriorToCurrentPoint, byref(enterEventMode), byref(terminateSimulation))
        # TODO: check status
        return enterEventMode, terminateSimulation


class FMU2Slave(_FMU2):

    def __init__(self, modelDescription, unzipDirectory, instanceName=None):

        super(FMU2Slave, self).__init__(modelDescription, unzipDirectory, instanceName, CO_SIMULATION)

        self.fmi2DoStep          = getattr(self.dll, 'fmi2DoStep')
        self.fmi2DoStep.argtypes = [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean]
        self.fmi2DoStep.restype  = fmi2Status

        self.fmi2GetBooleanStatus          = getattr(self.dll, 'fmi2GetBooleanStatus')
        self.fmi2GetBooleanStatus.argtypes = [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)]
        self.fmi2GetBooleanStatus.restype  = fmi2Status

    @fmi2Call
    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint=fmi2True):
        status = self.fmi2DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
        return status

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        status = self.fmi2GetBooleanStatus(self.component, kind, byref(value))
        # TODO: check status
        return value
