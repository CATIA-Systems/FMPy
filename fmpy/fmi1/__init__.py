# noinspection PyPep8

import os
import pathlib
from ctypes import *
from itertools import combinations
from .. import free, freeLibrary, platform, sharedLibraryExtension, calloc

fmi1Component      = c_void_p
fmi1ValueReference = c_uint
fmi1Real           = c_double
fmi1Integer        = c_int
fmi1Boolean        = c_char
fmi1String         = c_char_p

fmi1True  = 1
fmi1False = 0

fmi1UndefinedValueReference = -1

fmi1Status = c_int

fmi1CallbackLoggerTYPE         = CFUNCTYPE(None, fmi1Component, fmi1String, fmi1Status, fmi1String, fmi1String)
fmi1CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi1CallbackFreeMemoryTYPE     = CFUNCTYPE(None, c_void_p)
#fmi1StepFinishedTYPE           = CFUNCTYPE(None, fmi1Component, fmi1Status)
fmi1StepFinishedTYPE           = c_void_p

class fmi1CallbackFunctions(Structure):
    _fields_ = [('logger',         fmi1CallbackLoggerTYPE),
                ('allocateMemory', fmi1CallbackAllocateMemoryTYPE),
                ('freeMemory',     fmi1CallbackFreeMemoryTYPE),
                ('stepFinished',   fmi1StepFinishedTYPE)]

class fmi1EventInfo(Structure):
    _fields_ = [('iterationConverged',          fmi1Boolean),
                ('stateValueReferencesChanged', fmi1Boolean),
                ('stateValuesChanged',          fmi1Boolean),
                ('terminateSimulation',         fmi1Boolean),
                ('upcomingTimeEvent',           fmi1Boolean),
                ('nextEventTime',               fmi1Real)]

def logger(a, b, c, d, e):
    print(a, b, c, d, e)

def allocateMemory(nobj, size):
    return calloc(nobj, size)

def freeMemory(obj):
    free(obj)

def stepFinished(componentEnvironment, status):
    print(combinations, status)

callbacks = fmi1CallbackFunctions()
callbacks.logger               = fmi1CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
callbacks.freeMemory           = fmi1CallbackFreeMemoryTYPE(freeMemory)
#callbacks.stepFinished         = fmi1StepFinishedTYPE(stepFinished)
#callbacks.stepFinished = None


class _FMU(object):

    MODEL_EXCHANGE = 0
    CO_SIMULATION = 1

    def __init__(self, modelDescription, unzipDirectory, instanceName, fmiType):

        self.modelDescription = modelDescription
        self.unzipDirectory = unzipDirectory
        self.instanceName = instanceName
        self.fmiType = fmiType

        if fmiType == _FMU.MODEL_EXCHANGE:
            self.modelIdentifier = modelDescription.modelExchange.modelIdentifier
        else:
            self.modelIdentifier = modelDescription.coSimulation.modelIdentifier


class _FMU1(_FMU):

    def __init__(self, modelDescription, unzipDirectory, instanceName, fmiType):

        fmiType = _FMU.CO_SIMULATION if modelDescription.coSimulation is not None else _FMU.MODEL_EXCHANGE

        super(_FMU1, self).__init__(modelDescription, unzipDirectory, instanceName, fmiType)

        # load the shared library
        library = cdll.LoadLibrary(os.path.join(unzipDirectory, 'binaries', platform, self.modelIdentifier + sharedLibraryExtension))
        self.dll = library

        # common FMI 1.0 functions
        self.fmi1GetReal          = getattr(library, self.modelIdentifier  + '_fmiGetReal')
        self.fmi1GetReal.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)]
        self.fmi1GetReal.restype  = fmi1Status

        self.fmi1GetInteger = getattr(library, self.modelIdentifier  + '_fmiGetInteger')
        self.fmi1GetInteger.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)]
        self.fmi1GetInteger.restype = fmi1Status

        self.fmi1GetBoolean = getattr(library, self.modelIdentifier  + '_fmiGetBoolean')
        self.fmi1GetBoolean.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)]
        self.fmi1GetBoolean.restype = fmi1Status

        self.fmi1SetReal = getattr(library, self.modelIdentifier  + '_fmiSetReal')
        self.fmi1SetReal.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)]
        self.fmi1SetReal.restype = fmi1Status

        self.fmi1SetInteger = getattr(library, self.modelIdentifier  + '_fmiSetInteger')
        self.fmi1SetInteger.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)]
        self.fmi1SetInteger.restype = fmi1Status

        self.fmi1SetBoolean = getattr(library, self.modelIdentifier  + '_fmiSetBoolean')
        self.fmi1SetBoolean.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)]
        self.fmi1SetBoolean.restype = fmi1Status

        pass

    def instantiate(self, mimeType="application/x-fmu-sharedlibrary", timeout=0, visible=fmi1False,
                    interactive=fmi1False, functions=callbacks, loggingOn=fmi1False):

        fmuLocation = pathlib.Path(self.unzipDirectory).as_uri()

        self.component = self.fmi1InstantiateSlave(self.instanceName.encode('UTF-8'),
                                                   self.modelDescription.guid.encode('UTF-8'),
                                                   fmuLocation.encode('UTF-8'),
                                                   mimeType.encode('UTF-8'),
                                                   timeout,
                                                   visible,
                                                   interactive,
                                                   callbacks,
                                                   loggingOn)

    def initializeSlave(self, tStart=0.0, stopTime=None):
        stopTimeDefined = stopTime is not None
        tStop = stopTime if stopTimeDefined else 0
        status = self.fmi1InitializeSlave(self.component, tStart, stopTimeDefined, tStop)
        return status


    def doStep(self, currentCommunicationPoint, communicationStepSize, newStep=fmi1True):
        status = self.fmi1DoStep(self.component, currentCommunicationPoint, communicationStepSize, newStep)
        return status

    def terminateSlave(self):
        status = self.fmi1TerminateSlave(self.component)

    def freeSlaveInstance(self):
        self.fmi1FreeSlaveInstance(self.component)

        # unload the shared library
        freeLibrary(self.dll._handle)


class FMU1Slave(_FMU1):

    def __init__(self, modelDescription, unzipDirectory, instanceName):

        super(FMU1Slave, self).__init__(modelDescription, unzipDirectory, instanceName, _FMU.CO_SIMULATION)

        # FMI 1.0 Co-Simulation functions
        self.fmi1InstantiateSlave = getattr(self.dll, self.modelIdentifier + '_fmiInstantiateSlave')
        self.fmi1InstantiateSlave.argtypes = [fmi1String, fmi1String, fmi1String, fmi1String, fmi1Real, fmi1Boolean, fmi1Boolean, fmi1CallbackFunctions, fmi1Boolean]
        self.fmi1InstantiateSlave.restype = fmi1Component

        self.fmi1InitializeSlave = getattr(self.dll, self.modelIdentifier + '_fmiInitializeSlave')
        self.fmi1InitializeSlave.argtypes = [fmi1Component, fmi1Real, fmi1Boolean, fmi1Real]
        self.fmi1InitializeSlave.restype = fmi1Status

        self.fmi1DoStep = getattr(self.dll, self.modelIdentifier + '_fmiDoStep')
        self.fmi1DoStep.argtypes = [fmi1Component, fmi1Real, fmi1Real, fmi1Boolean]
        self.fmi1DoStep.restype = fmi1Status

        self.fmi1TerminateSlave = getattr(self.dll, self.modelIdentifier + '_fmiTerminateSlave')
        self.fmi1TerminateSlave.argtypes = [fmi1Component]
        self.fmi1TerminateSlave.restype = fmi1Status

        self.fmi1FreeSlaveInstance = getattr(self.dll, self.modelIdentifier + '_fmiFreeSlaveInstance')
        self.fmi1FreeSlaveInstance.argtypes = [fmi1Component]
        self.fmi1FreeSlaveInstance.restype = fmi1Status


class FMU1Model(_FMU1):

    def __init__(self, modelDescription, unzipDirectory, instanceName):

        super(FMU1Model, self).__init__(modelDescription, unzipDirectory, instanceName, _FMU.MODEL_EXCHANGE)

        # FMI 1.0 Model Exchange functions
        self.fmi1InstantiateModel = getattr(self.dll, self.modelIdentifier + '_fmiInstantiateModel')
        self.fmi1InstantiateModel.argtypes = [fmi1String, fmi1String, fmi1CallbackFunctions, fmi1Boolean]
        self.fmi1InstantiateModel.restype = fmi1Component

        self.fmi1SetTime = getattr(self.dll, self.modelIdentifier + '_fmiSetTime')
        self.fmi1SetTime.argtypes = [fmi1Component, fmi1Real]
        self.fmi1SetTime.restype = fmi1Status

        self.fmi1Initialize = getattr(self.dll, self.modelIdentifier + '_fmiInitialize')
        self.fmi1Initialize.argtypes = [fmi1Component, fmi1Boolean, fmi1Real, fmi1EventInfo]
        self.fmi1Initialize.restype = fmi1Status

        self.fmi1GetContinuousStates = getattr(self.dll, self.modelIdentifier + '_fmiGetContinuousStates')
        self.fmi1GetContinuousStates.argtypes = [fmi1Component, POINTER(fmi1Real), c_size_t]
        self.fmi1GetContinuousStates.restype = fmi1Status

        self.fmi1GetDerivatives = getattr(self.dll, self.modelIdentifier + '_fmiGetDerivatives')
        self.fmi1GetDerivatives.argtypes = [fmi1Component, POINTER(fmi1Real), c_size_t]
        self.fmi1GetDerivatives.restype = fmi1Status

        self.fmi1SetContinuousStates = getattr(self.dll, self.modelIdentifier + '_fmiSetContinuousStates')
        self.fmi1SetContinuousStates.argtypes = [fmi1Component, POINTER(fmi1Real), c_size_t]
        self.fmi1SetContinuousStates.restype = fmi1Status

        self.fmi1CompletedIntegratorStep = getattr(self.dll, self.modelIdentifier + '_fmiCompletedIntegratorStep')
        self.fmi1CompletedIntegratorStep.argtypes = [fmi1Component, fmi1Boolean]
        self.fmi1CompletedIntegratorStep.restype = fmi1Status

        self.fmi1GetEventIndicators = getattr(self.dll, self.modelIdentifier + '_fmiGetEventIndicators')
        self.fmi1GetEventIndicators.argtypes = [fmi1Component, POINTER(fmi1Real), c_size_t]
        self.fmi1GetEventIndicators.restype = fmi1Status

        self.fmi1EventUpdate = getattr(self.dll, self.modelIdentifier + '_fmiEventUpdate')
        self.fmi1EventUpdate.argtypes = [fmi1Component, fmi1Boolean, fmi1EventInfo]
        self.fmi1EventUpdate.restype = fmi1Status

        self.fmi1Terminate = getattr(self.dll, self.modelIdentifier + '_fmiTerminate')
        self.fmi1Terminate.argtypes = [fmi1Component]
        self.fmi1Terminate.restype = fmi1Status

        self.fmi1FreeModelInstance = getattr(self.dll, self.modelIdentifier + '_fmiFreeModelInstance')
        self.fmi1FreeModelInstance.argtypes = [fmi1Component]
        self.fmi1FreeModelInstance.restype = fmi1Status
