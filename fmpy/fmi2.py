# noinspection PyPep8

import os
from ctypes import *
from itertools import combinations
from lxml import etree
from . import free, freeLibrary, platform, sharedLibraryExtension, calloc, FMIType
from .fmi1 import _FMU


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


def logger(a, b, c, d, e, f):
    print(a, b, c, d, e, f)

def allocateMemory(nobj, size):
    return calloc(nobj, size)

def freeMemory(obj):
    free(obj)

def stepFinished(componentEnvironment, status):
    print(combinations, status)

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

        self.fmi2SetReal          = getattr(self.dll, 'fmi2SetReal')
        self.fmi2SetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2SetReal.restype  = fmi2Status

        self.fmi2SetInteger          = getattr(self.dll, 'fmi2SetInteger')
        self.fmi2SetInteger.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Integer)]
        self.fmi2SetInteger.restype  = fmi2Status

        self.fmi2SetBoolean          = getattr(self.dll, 'fmi2SetBoolean')
        self.fmi2SetBoolean.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Boolean)]
        self.fmi2SetBoolean.restype  = fmi2Status

        self.fmi2GetBooleanStatus          = getattr(self.dll, 'fmi2GetBooleanStatus')
        self.fmi2GetBooleanStatus.argtypes = [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)]
        self.fmi2GetBooleanStatus.restype  = fmi2Status

        self.fmi2Terminate          = getattr(self.dll, 'fmi2Terminate')
        self.fmi2Terminate.argtypes = [fmi2Component]
        self.fmi2Terminate.restype  = fmi2Status

        self.fmi2FreeInstance          = getattr(self.dll, 'fmi2FreeInstance')
        self.fmi2FreeInstance.argtypes = [fmi2Component]
        self.fmi2FreeInstance.restype  = None

    def instantiate(self):

        kind = fmi2ModelExchange if self.fmiType == FMIType.MODEL_EXCHANGE else fmi2CoSimulation

        self.component = self.fmi2Instantiate(self.instanceName.encode('utf-8'),
                                              kind,
                                              self.modelDescription.guid.encode('utf-8'),
                                              self.fmuLocation.encode('utf-8'),
                                              byref(callbacks), fmi2False,
                                              fmi2False)

    def setupExperiment(self, tolerance, startTime, stopTime=None):

        toleranceDefined = tolerance is not None

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = stopTime is not None

        if stopTime is None:
            stopTime = 0.0

        status = self.fmi2SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined,
                                          stopTime)

    def enterInitializationMode(self):
        status = self.fmi2EnterInitializationMode(self.component)
        return status

    def exitInitializationMode(self):
        status = self.fmi2ExitInitializationMode(self.component)
        return status

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        status = self.fmi2GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getReal(self, vr):
        value = (fmi2Real * len(vr))()
        status = self.fmi2GetReal(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        status = self.fmi2SetReal(self.component, vr, len(vr), value)

    def terminate(self):
        status = self.fmi2Terminate(self.component)

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)

        # unload the shared library
        freeLibrary(self.dll._handle)


class FMU2Slave(_FMU2):

    def __init__(self, modelDescription, unzipDirectory, instanceName=None):

        super(FMU2Slave, self).__init__(modelDescription, unzipDirectory, instanceName, FMIType.CO_SIMULATION)

        self.fmi2DoStep          = getattr(self.dll, 'fmi2DoStep')
        self.fmi2DoStep.argtypes = [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean]
        self.fmi2DoStep.restype  = fmi2Status

    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint=fmi2True):
        status = self.fmi2DoStep(self.component, currentCommunicationPoint, communicationStepSize, fmi2True)
        return status
