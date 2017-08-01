# noinspection PyPep8

import os
import pathlib
import numpy as np
from ctypes import *
from . import free, freeLibrary, platform, sharedLibraryExtension, calloc

fmi1Component      = c_void_p
fmi1ValueReference = c_uint
fmi1Real           = c_double
fmi1Integer        = c_int
fmi1Boolean        = c_char
fmi1String         = c_char_p

fmi1True  = b'\x01'
fmi1False = b'\x00'

fmi1UndefinedValueReference = -1

fmi1Status = c_int

fmi1OK      = 0
fmi1Warning = 1
fmi1Discard = 2
fmi1Error   = 3
fmi1Fatal   = 4

fmi1CallbackLoggerTYPE         = CFUNCTYPE(None, fmi1Component, fmi1String, fmi1Status, fmi1String, fmi1String)
fmi1CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi1CallbackFreeMemoryTYPE     = CFUNCTYPE(None, c_void_p)
# fmi1StepFinishedTYPE           = CFUNCTYPE(None, fmi1Component, fmi1Status)
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


def logger(component, instanceName, status, category, message):
    if status == fmi1Warning:
        print('[WARNING]', message)
    elif status > fmi1Warning:
        print('[ERROR]', message)


def allocateMemory(nobj, size):
    return calloc(nobj, size)


def freeMemory(obj):
    free(obj)


def stepFinished(componentEnvironment, status):
    pass


callbacks = fmi1CallbackFunctions()
callbacks.logger               = fmi1CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
callbacks.freeMemory           = fmi1CallbackFreeMemoryTYPE(freeMemory)
#callbacks.stepFinished         = fmi1StepFinishedTYPE(stepFinished)
callbacks.stepFinished = None


class _FMU(object):

    def __init__(self, guid, modelIdentifier, unzipDirectory, instanceName, logFMICalls=False):

        self.guid = guid
        self.modelIdentifier = modelIdentifier
        self.unzipDirectory = unzipDirectory
        self.instanceName = instanceName if instanceName is not None else self.modelIdentifier
        self.fmuLocation = pathlib.Path(self.unzipDirectory).as_uri()
        self.logFMICalls = logFMICalls

        # remember the current working directory
        work_dir = os.getcwd()

        library_dir = os.path.join(unzipDirectory, 'binaries', platform)

        # change to the library directory as some DLLs expect this to resolve dependencies
        os.chdir(library_dir)

        # load the shared library
        library_path = str(os.path.join(library_dir, self.modelIdentifier + sharedLibraryExtension))
        self.dll = cdll.LoadLibrary(library_path)

        # change back to the working directory
        os.chdir(work_dir)

        self.component = None

    def _print_fmi_args(self, fname, argnames, argtypes, args, restype, res):

        f = '[FMI] ' + fname + '('

        l = []

        for n, t, v in zip(argnames, argtypes, args):

            a = n + '='

            if t == c_void_p:  # component pointer
                a += hex(v)
            elif t == POINTER(c_uint):  # value references
                a += '[' + ', '.join(map(str, v)) + ']'
            elif t == POINTER(c_double):
                if hasattr(v, '__len__'):  # double array
                    a += '[' + ', '.join(map(str, v)) + ']'
                elif v == self._px:  # continuous states
                    a += '[' + ', '.join(map(str, self.x)) + ']'
                elif v == self._pdx:  # derivatives
                    a += '[' + ', '.join(map(str, self.dx)) + ']'
                elif v == self._pz:  # event indicators
                    a += '[' + ', '.join(map(str, self.z)) + ']'
                else:
                    a += str(v.contents.value)
            else:
                a += str(v)

            l.append(a)

        f += ', '.join(l) + ')'

        if restype == c_int:

            f += ' -> '

            if res == 0:
                f += 'OK'
            elif res == 1:
                f += 'WARNING'
            elif res == 2:
                f += 'DISCARD'
            elif res == 3:
                f += 'ERROR'
            elif res == 4:
                f += 'FATAL'
            elif res == 5:
                f += 'PENDING'
            else:
                f += str(res)
        elif restype == c_void_p:
            f += ' -> ' + hex(res)

        print(f)


class _FMU1(_FMU):

    def __init__(self, **kwargs):

        super(_FMU1, self).__init__(**kwargs)

        # common FMI 1.0 functions

        self._fmi1Function('GetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)],
                           fmi1Status)

        self._fmi1Function('GetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)],
                           fmi1Status)

        self._fmi1Function('GetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)],
                           fmi1Status)

        self._fmi1Function('GetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1String)],
                           fmi1Status)

        self._fmi1Function('SetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)],
                           fmi1Status)

        self._fmi1Function('SetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)],
                           fmi1Status)

        self._fmi1Function('SetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)],
                           fmi1Status)

        self._fmi1Function('SetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1String)],
                           fmi1Status)

    def _fmi1Function(self, name, argnames, argtypes, restype):

        f = getattr(self.dll, self.modelIdentifier + '_fmi' + name)
        f.argtypes = argtypes
        f.restype = restype

        def w(*args, **kwargs):

            res = f(*args, **kwargs)

            if self.logFMICalls:
                self._print_fmi_args('fmi' + name, argnames, argtypes, args, restype, res)

            if restype == fmi1Status:
                # check the status code
                if res > 1:
                    raise Exception("FMI call failed with status %d." % res)

            return res

        setattr(self, 'fmi1' + name, w)

    def assertNoError(self, status):
        if status not in [fmi1OK, fmi1Warning]:
            raise Exception("FMI call failed")

    def getReal(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))()
        status = self.fmi1GetReal(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))()
        status = self.fmi1GetInteger(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))()
        status = self.fmi1GetBoolean(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(map(lambda b: 0 if b == fmi1False else 1, value))

    def getString(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1String * len(vr))()
        status = self.fmi1GetString(self.component, vr, len(vr), value)
        self.assertNoError(status)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))(*value)
        status = self.fmi1SetReal(self.component, vr, len(vr), value)
        self.assertNoError(status)

    def setInteger(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))(*value)
        status = self.fmi1SetInteger(self.component, vr, len(vr), value)
        self.assertNoError(status)

    def setBoolean(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))(*value)
        status = self.fmi1SetBoolean(self.component, vr, len(vr), value)
        self.assertNoError(status)

    def setString(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = map(lambda s: s.encode('utf-8'), value)
        value = (fmi1String * len(vr))(*value)
        status = self.fmi1SetString(self.component, vr, len(vr), value)
        self.assertNoError(status)


class FMU1Slave(_FMU1):

    def __init__(self, **kwargs):

        super(FMU1Slave, self).__init__(**kwargs)

        # FMI 1.0 Co-Simulation functions
        self._fmi1Function('InstantiateSlave',
                           ['instanceName', 'guid', 'fmuLocation', 'mimeType', 'timeout', 'visible', 'interactive', 'functions', 'loggingOn'],
                           [fmi1String, fmi1String, fmi1String, fmi1String, fmi1Real, fmi1Boolean, fmi1Boolean, fmi1CallbackFunctions, fmi1Boolean],
                           fmi1Component)

        self._fmi1Function('InitializeSlave',
                           ['component', 'tStart', 'stopTimeDefined', 'tStop'],
                           [fmi1Component, fmi1Real, fmi1Boolean, fmi1Real],
                           fmi1Status)

        self._fmi1Function('DoStep',
                           ['component', 'currentCommunicationPoint', 'communicationStepSize', 'newStep'],
                           [fmi1Component, fmi1Real, fmi1Real, fmi1Boolean],
                           fmi1Status)

        self._fmi1Function('TerminateSlave',
                           ['component'],
                           [fmi1Component],
                           fmi1Status)

        self._fmi1Function('FreeSlaveInstance',
                           ['component'],
                           [fmi1Component],
                           None)

    def instantiate(self, mimeType='application/x-fmu-sharedlibrary', timeout=0, visible=fmi1False,
                    interactive=fmi1False, functions=callbacks, loggingOn=fmi1False):

        self.component = self.fmi1InstantiateSlave(self.instanceName.encode('UTF-8'),
                                                   self.guid.encode('UTF-8'),
                                                   self.fmuLocation.encode('UTF-8'),
                                                   mimeType.encode('UTF-8'),
                                                   timeout,
                                                   visible,
                                                   interactive,
                                                   functions,
                                                   loggingOn)

    def initialize(self, tStart=0.0, stopTime=None):
        stopTimeDefined = fmi1True if stopTime is not None else fmi1False
        tStop = stopTime if stopTime is not None else 0.0
        return self.fmi1InitializeSlave(self.component, tStart, stopTimeDefined, tStop)

    def terminate(self):
        return self.fmi1TerminateSlave(self.component)

    def freeInstance(self):
        self.fmi1FreeSlaveInstance(self.component)
        # unload the shared library
        freeLibrary(self.dll._handle)

    def doStep(self, currentCommunicationPoint, communicationStepSize, newStep=fmi1True):
        return self.fmi1DoStep(self.component, currentCommunicationPoint, communicationStepSize, newStep)


class FMU1Model(_FMU1):

    def __init__(self, numberOfContinuousStates, numberOfEventIndicators, **kwargs):

        super(FMU1Model, self).__init__(**kwargs)

        self.eventInfo = fmi1EventInfo()

        self.x = np.zeros(numberOfContinuousStates)
        self.dx = np.zeros(numberOfContinuousStates)
        self.z = np.zeros(numberOfEventIndicators)

        self._px = self.x.ctypes.data_as(POINTER(fmi1Real))
        self._pdx = self.dx.ctypes.data_as(POINTER(fmi1Real))
        self._pz = self.z.ctypes.data_as(POINTER(fmi1Real))

        self._fmi1Function('InstantiateModel',
                           ['instanceName', 'guid', 'functions', 'loggingOn'],
                           [fmi1String, fmi1String, fmi1CallbackFunctions, fmi1Boolean],
                           fmi1Component)

        self._fmi1Function('SetTime',
                           ['component', 'time'],
                           [fmi1Component, fmi1Real],
                           fmi1Status)

        self._fmi1Function('Initialize',
                           ['component', 'toleranceControlled', 'relativeTolerance', 'eventInfo'],
                           [fmi1Component, fmi1Boolean, fmi1Real, POINTER(fmi1EventInfo)],
                           fmi1Status)

        self._fmi1Function('GetContinuousStates',
                           ['component', 'states', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t],
                           fmi1Status)

        self._fmi1Function('GetDerivatives',
                           ['component', 'derivatives', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t],
                           fmi1Status)

        self._fmi1Function('SetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t],
                           fmi1Status)

        self._fmi1Function('CompletedIntegratorStep',
                           ['component', 'callEventUpdate'],
                           [fmi1Component, POINTER(fmi1Boolean)],
                           fmi1Status)

        self._fmi1Function('GetEventIndicators',
                           ['component', 'eventIndicators', 'ni'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t],
                           fmi1Status)

        self._fmi1Function('EventUpdate',
                           ['component', 'intermediateResults', 'eventInfo'],
                           [fmi1Component, fmi1Boolean, POINTER(fmi1EventInfo)],
                           fmi1Status)

        self._fmi1Function('Terminate',
                           ['component'],
                           [fmi1Component],
                           fmi1Status)

        self._fmi1Function('FreeModelInstance',
                           ['component'],
                           [fmi1Component],
                           None)

    def instantiate(self, functions=callbacks, loggingOn=fmi1False):
        self.component = self.fmi1InstantiateModel(self.instanceName.encode('UTF-8'),
                                                   self.guid.encode('UTF-8'),
                                                   functions,
                                                   loggingOn)

    def setTime(self, time):
        return self.fmi1SetTime(self.component, time)

    def initialize(self, toleranceControlled=fmi1False, relativeTolerance=0.0):
        return self.fmi1Initialize(self.component, toleranceControlled, relativeTolerance, byref(self.eventInfo))

    def getContinuousStates(self):
        return self.fmi1GetContinuousStates(self.component, self._px, self.x.size)

    def setContinuousStates(self):
        return self.fmi1SetContinuousStates(self.component, self._px, self.x.size)

    def getDerivatives(self):
        return self.fmi1GetDerivatives(self.component, self._pdx, self.dx.size)

    def completedIntegratorStep(self):
        stepEvent = fmi1Boolean()
        status = self.fmi1CompletedIntegratorStep(self.component, byref(stepEvent))
        return stepEvent != fmi1False

    def getEventIndicators(self):
        return self.fmi1GetEventIndicators(self.component, self._pz, self.z.size)

    def eventUpdate(self, intermediateResults=fmi1False):
        return self.fmi1EventUpdate(self.component, intermediateResults, byref(self.eventInfo))

    def terminate(self):
        return self.fmi1Terminate(self.component)

    def freeInstance(self):
        self.fmi1FreeModelInstance(self.component)
        # unload the shared library
        freeLibrary(self.dll._handle)
