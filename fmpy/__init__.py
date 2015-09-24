import os

from lxml import etree
from ctypes import *
from itertools import combinations

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

calloc          = cdll.msvcrt.calloc
calloc.argtypes = [c_size_t, c_size_t]
calloc.restype  = c_void_p

free = cdll.msvcrt.free
free.argtypes = [c_void_p]

def logger(a, b, c, d, e):
    print a, b, c, d, e

def allocateMemory(nobj, size):
    return calloc(nobj, size)

def freeMemory(obj):
    free(obj)

def stepFinished(componentEnvironment, status):
    print combinations, status

class fmi2CallbackFunctions(Structure):
    _fields_ = [('logger',               fmi2CallbackLoggerTYPE),
                ('allocateMemory',       fmi2CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi2CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi2StepFinishedTYPE),
                ('componentEnvironment', fmi2ComponentEnvironment)]

callbacks = fmi2CallbackFunctions()
callbacks.logger               = fmi2CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
callbacks.stepFinished         = fmi2StepFinishedTYPE(stepFinished)
callbacks.freeMemory           = fmi2CallbackFreeMemoryTYPE(freeMemory)
callbacks.componentEnvironment = None

variables = {}

class ScalarVariable(object):

    def __init__(self, name, valueReference):
        self.name = name
        self.valueReference = valueReference
        self.description = None
        self.start = None
        self.causality = None
        self.variability = None

class FMU2(object):

    def __init__(self, unzipdir):

        self.unzipdir = unzipdir

        tree = etree.parse(os.path.join(unzipdir, 'modelDescription.xml'))

        root = tree.getroot()

        self.guid       = root.get('guid')
        self.fmiVersion = root.get('fmiVersion')
        self.modelName  = root.get('modelName')
        self.causality  = root.get('causality')
        self.variability  = root.get('variability')

        modelVariables = root.find('ModelVariables')

        self.variables = {}

        for variable in modelVariables:
            sv = ScalarVariable(name=variable.get('name'), valueReference=int(variable.get('valueReference')))
            sv.description = variable.get('description')
            sv.start = variable.get('start')
            self.variables[sv.name] = sv

        library = cdll.LoadLibrary(os.path.join(unzipdir, 'binaries', 'win32', 'bouncingBall.dll'))

        self.fmi2Instantiate = getattr(library, 'fmi2Instantiate')
        self.fmi2Instantiate.argtypes = [fmi2String, fmi2Type, fmi2String, fmi2String, POINTER(fmi2CallbackFunctions), fmi2Boolean, fmi2Boolean]
        self.fmi2Instantiate.restype = fmi2ComponentEnvironment

        self.fmi2SetupExperiment          = getattr(library, 'fmi2SetupExperiment')
        self.fmi2SetupExperiment.argtypes = [fmi2Component, fmi2Boolean, fmi2Real, fmi2Real, fmi2Boolean, fmi2Real]
        self.fmi2SetupExperiment.restype  = fmi2Status

        self.fmi2EnterInitializationMode          = getattr(library, 'fmi2EnterInitializationMode')
        self.fmi2EnterInitializationMode.argtypes = [fmi2Component]
        self.fmi2EnterInitializationMode.restype  = fmi2Status

        self.fmi2ExitInitializationMode          = getattr(library, 'fmi2ExitInitializationMode')
        self.fmi2ExitInitializationMode.argtypes = [fmi2Component]
        self.fmi2ExitInitializationMode.restype  = fmi2Status

        self.fmi2DoStep          = getattr(library, 'fmi2DoStep')
        self.fmi2DoStep.argtypes = [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean]
        self.fmi2DoStep.restype  = fmi2Status

        self.fmi2GetReal          = getattr(library, 'fmi2GetReal')
        self.fmi2GetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
        self.fmi2GetReal.restype  = fmi2Status

        self.fmi2GetBooleanStatus          = getattr(library, 'fmi2GetBooleanStatus')
        self.fmi2GetBooleanStatus.argtypes = [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)]
        self.fmi2GetBooleanStatus.restype  = fmi2Status

        self.fmi2Terminate          = getattr(library, 'fmi2Terminate')
        self.fmi2Terminate.argtypes = [fmi2Component]
        self.fmi2Terminate.restype  = fmi2Status

        self.fmi2FreeInstance          = getattr(library, 'fmi2FreeInstance')
        self.fmi2FreeInstance.argtypes = [fmi2Component]
        self.fmi2FreeInstance.restype  = None

    def instantiate(self, instance_name, kind):
        self.component = self.fmi2Instantiate(instance_name, kind, self.guid, 'file://' + self.unzipdir, byref(callbacks), fmi2False, fmi2False)

    def setupExperiment(self, tolerance, startTime, stopTime=None):

        toleranceDefined = tolerance is not None

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = stopTime is not None

        if stopTime is None:
            stopTime = 0.0

        status = self.fmi2SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)

    def enterInitializationMode(self):
        status = self.fmi2EnterInitializationMode(self.component)

    def exitInitializationMode(self):
        status = self.fmi2ExitInitializationMode(self.component)

    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint):
        status = self.fmi2DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
        return status

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        status = self.fmi2GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getReal(self, vr):
        value = (fmi2Real * len(vr))()
        status = self.fmi2GetReal(self.component, vr, len(vr), value)
        return list(value)

    def terminate(self):
        status = self.fmi2Terminate(self.component)

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)
