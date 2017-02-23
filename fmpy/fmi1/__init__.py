# noinspection PyPep8

import os
import pathlib
from ctypes import *
from itertools import combinations
from lxml import etree
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


class FMU1(object):

    def __init__(self, modelDescription, unzipDirectory, instanceName):

        self.modelDescription = modelDescription
        self.unzipDirectory = unzipDirectory
        self.instanceName = instanceName

        if modelDescription.coSimulation is not None:
            modelIdentifier = modelDescription.coSimulation.modelIdentifier
        else:
            modelIdentifier = modelDescription.modelExchange.modelIdentifier

        # load the shared library
        library = cdll.LoadLibrary(os.path.join(unzipDirectory, 'binaries', platform, modelIdentifier + sharedLibraryExtension))
        self.dll = library

        self.fmi1InstantiateSlave = getattr(library, modelIdentifier + '_fmiInstantiateSlave')
        self.fmi1InstantiateSlave.argtypes = [fmi1String, fmi1String, fmi1String, fmi1String, fmi1Real, fmi1Boolean, fmi1Boolean, fmi1CallbackFunctions, fmi1Boolean]
        self.fmi1InstantiateSlave.restype = fmi1Component

        self.fmi1InitializeSlave = getattr(library, modelIdentifier + '_fmiInitializeSlave')
        self.fmi1InitializeSlave.argtypes = [fmi1Component, fmi1Real, fmi1Boolean, fmi1Real]
        self.fmi1InitializeSlave.restype = fmi1Status

        self.fmi1DoStep = getattr(library, modelIdentifier + '_fmiDoStep')
        self.fmi1DoStep.argtypes = [fmi1Component, fmi1Real, fmi1Real, fmi1Boolean]
        self.fmi1DoStep.restype = fmi1Status

        self.fmi1TerminateSlave = getattr(library, modelIdentifier + '_fmiTerminateSlave')
        self.fmi1TerminateSlave.argtypes = [fmi1Component]
        self.fmi1TerminateSlave.restype = fmi1Status

        self.fmi1FreeSlaveInstance = getattr(library, modelIdentifier + '_fmiFreeSlaveInstance')
        self.fmi1FreeSlaveInstance.argtypes = [fmi1Component]
        self.fmi1FreeSlaveInstance.restype = fmi1Status

        # common FMI functions
        self.fmi1GetReal          = getattr(library, modelIdentifier + '_fmiGetReal')
        self.fmi1GetReal.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)]
        self.fmi1GetReal.restype  = fmi1Status

        self.fmi1GetInteger = getattr(library, modelIdentifier + '_fmiGetInteger')
        self.fmi1GetInteger.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)]
        self.fmi1GetInteger.restype = fmi1Status

        self.fmi1GetBoolean = getattr(library, modelIdentifier + '_fmiGetBoolean')
        self.fmi1GetBoolean.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)]
        self.fmi1GetBoolean.restype = fmi1Status

        self.fmi1SetReal = getattr(library, modelIdentifier + '_fmiSetReal')
        self.fmi1SetReal.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)]
        self.fmi1SetReal.restype = fmi1Status

        self.fmi1SetInteger = getattr(library, modelIdentifier + '_fmiSetInteger')
        self.fmi1SetInteger.argtypes = [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)]
        self.fmi1SetInteger.restype = fmi1Status

        self.fmi1SetBoolean = getattr(library, modelIdentifier + '_fmiSetBoolean')
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
