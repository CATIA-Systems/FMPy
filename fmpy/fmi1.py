""" FMI 1.0 interface """

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

fmi1StatusKind = c_int

fmi1DoStepStatus       = 0
fmi1PendingStatus      = 1
fmi1LastSuccessfulTime = 2


class fmi1CallbackFunctions(Structure):

    _fields_ = [('logger',         fmi1CallbackLoggerTYPE),
                ('allocateMemory', fmi1CallbackAllocateMemoryTYPE),
                ('freeMemory',     fmi1CallbackFreeMemoryTYPE),
                ('stepFinished',   fmi1StepFinishedTYPE)]

    def __str__(self):
        return 'fmi1CallbackFunctions(' \
               'logger=%s, ' \
               'allocateMemory=%s, ' \
               'freeMemory=%s, ' \
               'stepFinished=%s)' % (self.logger,
                                     self.allocateMemory,
                                     self.freeMemory,
                                     self.stepFinished)


class fmi1EventInfo(Structure):

    _fields_ = [('iterationConverged',          fmi1Boolean),
                ('stateValueReferencesChanged', fmi1Boolean),
                ('stateValuesChanged',          fmi1Boolean),
                ('terminateSimulation',         fmi1Boolean),
                ('upcomingTimeEvent',           fmi1Boolean),
                ('nextEventTime',               fmi1Real)]

    def __str__(self):
        return 'fmi1EventInfo(' \
               'iterationConverged=%s, ' \
               'stateValueReferencesChanged=%s, ' \
               'stateValuesChanged=%s, ' \
               'terminateSimulation=%s, ' \
               'upcomingTimeEvent=%s, ' \
               'nextEventTime=%s)' % (self.iterationConverged,
                                      self.stateValueReferencesChanged,
                                      self.stateValuesChanged,
                                      self.terminateSimulation,
                                      self.upcomingTimeEvent,
                                      self.nextEventTime)


def printLogMessage(component, instanceName, status, category, message):
    """ Print the FMU's log messages to the command line (works for both FMI 1.0 and 2.0) """

    label = ['OK', 'WARNING', 'DISCARD', 'ERROR', 'FATAL', 'PENDING'][status]
    print("[%s] %s" % (label, message))


def allocateMemory(nobj, size):
    return calloc(nobj, size)


def freeMemory(obj):
    free(obj)


def stepFinished(componentEnvironment, status):
    pass


class _FMU(object):
    """ Base class for all FMUs """

    def __init__(self, guid, modelIdentifier, unzipDirectory, instanceName=None, libraryPath=None, fmiCallLogger=None):
        """
        Parameters:
            guid             the GUI from the modelDescription.xml
            modelIdentifier  the model identifier from the modelDescription.xml
            unzipDirectory   folder where the FMU has been extracted
            instanceName     the name of the FMU instance
            libraryPath      path to the shared library
            fmiCallLogger    logger callback that takes a message as input
        """

        self.guid = guid
        self.modelIdentifier = modelIdentifier
        self.unzipDirectory = unzipDirectory
        self.instanceName = instanceName if instanceName is not None else self.modelIdentifier
        self.fmiCallLogger = fmiCallLogger

        # remember the current working directory
        work_dir = os.getcwd()

        if libraryPath is None:
            library_dir = os.path.join(unzipDirectory, 'binaries', platform)
            libraryPath = str(os.path.join(library_dir, self.modelIdentifier + sharedLibraryExtension))
        else:
            library_dir = os.path.dirname(libraryPath)

        # change to the library directory as some DLLs expect this to resolve dependencies
        os.chdir(library_dir)

        # load the shared library
        self.dll = cdll.LoadLibrary(libraryPath)

        # change back to the working directory
        os.chdir(work_dir)

        self.component = None

        self.callbacks = None
        " Reference to the callbacks struct (to save it from GC)"

    def freeLibrary(self):
        # unload the shared library
        freeLibrary(self.dll._handle)

    def _log_fmi_args(self, fname, argnames, argtypes, args, restype, res):
        """ Format FMI arguments and pass them to the logger """

        f = fname + '('

        l = []

        for i, (n, t, v) in enumerate(zip(argnames, argtypes, args)):

            a = n + '='

            if t == c_void_p:
                # component pointer
                a += hex(v)
            elif t == POINTER(c_uint):
                # value references
                a += '[' + ', '.join(map(str, v)) + ']'
            elif t == POINTER(c_double):
                if hasattr(v, '__len__'):
                    # c_double_Array_N
                    a += '[' + ', '.join(map(str, v)) + ']'
                else:
                    # double pointers are always flowed by the size of the array
                    arr = np.ctypeslib.as_array(v, (args[i+1],))
                    a += '[' + ', '.join(map(str, arr)) + ']'
            elif hasattr(v, '_obj'):
                # byref object
                if hasattr(v._obj, 'value'):
                    # pointer (e.g. c_char_p)
                    a += str(v._obj.value)
                else:
                    # struct
                    a += str(v._obj)
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

        self.fmiCallLogger(f)


class _FMU1(_FMU):
    """ Base class for FMI 1.0 FMUs """

    def __init__(self, **kwargs):

        super(_FMU1, self).__init__(**kwargs)

        # Inquire version numbers of header files
        self._fmi1Function('GetVersion', [], [], fmi1String)

        self._fmi1Function('SetDebugLogging', ['component', 'loggingOn'], [fmi1Component, fmi1Boolean], fmi1Status)

        # Data Exchange Functions
        self._fmi1Function('GetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)])

        self._fmi1Function('GetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)])

        self._fmi1Function('GetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)])

        self._fmi1Function('GetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1String)])

        self._fmi1Function('SetReal',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Real)])

        self._fmi1Function('SetInteger',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer)])

        self._fmi1Function('SetBoolean',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Boolean)])

        self._fmi1Function('SetString',
                           ['component', 'vr', 'nvr', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1String)])

    def _fmi1Function(self, name, argnames, argtypes, restype=fmi1Status):
        """ Add an FMI 1.0 function to this instance and add a wrapper that allows
        logging and checks the return code if the return type if fmi1Status

        Parameters:
            fname     the name of the function (without 'fmi' prefix)
            argnames  names of the arguments
            argtypes  types of the arguments
            restype   return type
        """

        # get the exported function form the shared library
        f = getattr(self.dll, self.modelIdentifier + '_fmi' + name)
        f.argtypes = argtypes
        f.restype = restype

        def w(*args):
            """ Wrapper function for the FMI call """

            # call the FMI function
            res = f(*args)

            if self.fmiCallLogger is not None:
                # log the call
                self._log_fmi_args('fmi' + name, argnames, argtypes, args, restype, res)

            if restype == fmi1Status:
                # check the status code
                if res > fmi1Warning:
                    raise Exception("FMI call failed with status %d." % res)

            return res

        # add the function to the instance
        setattr(self, 'fmi1' + name, w)

    # Inquire version numbers of header files

    def getVersion(self):
        version = self.fmi1GetVersion()
        return version.decode('utf-8')

    def setDebugLogging(self, loggingOn):
        self.fmi1SetDebugLogging(self.component, fmi1True if loggingOn else fmi1False)

    # Data Exchange Functions

    def getReal(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))()
        self.fmi1GetReal(self.component, vr, len(vr), value)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))()
        self.fmi1GetInteger(self.component, vr, len(vr), value)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))()
        self.fmi1GetBoolean(self.component, vr, len(vr), value)
        return list(map(lambda b: 0 if b == fmi1False else 1, value))

    def getString(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1String * len(vr))()
        self.fmi1GetString(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))(*value)
        self.fmi1SetReal(self.component, vr, len(vr), value)

    def setInteger(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))(*value)
        self.fmi1SetInteger(self.component, vr, len(vr), value)

    def setBoolean(self, vr, value):
        # convert value to a byte string
        s = b''
        for v in value:
            s += fmi1True if v else fmi1False

        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))(s)
        self.fmi1SetBoolean(self.component, vr, len(vr), value)

    def setString(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = map(lambda s: s.encode('utf-8'), value)
        value = (fmi1String * len(vr))(*value)
        self.fmi1SetString(self.component, vr, len(vr), value)


class FMU1Slave(_FMU1):
    """ An FMI 1.0 Co-Simulation FMU """

    def __init__(self, **kwargs):

        super(FMU1Slave, self).__init__(**kwargs)

        # Inquire version numbers of header files
        self._fmi1Function('GetTypesPlatform', [], [], fmi1String)

        # Creation and destruction of slave instances and setting debug status
        self._fmi1Function('InstantiateSlave',
                           ['instanceName', 'guid', 'fmuLocation', 'mimeType', 'timeout', 'visible', 'interactive', 'functions', 'loggingOn'],
                           [fmi1String, fmi1String, fmi1String, fmi1String, fmi1Real, fmi1Boolean, fmi1Boolean, fmi1CallbackFunctions, fmi1Boolean],
                           fmi1Component)

        self._fmi1Function('InitializeSlave',
                           ['component', 'tStart', 'stopTimeDefined', 'tStop'],
                           [fmi1Component, fmi1Real, fmi1Boolean, fmi1Real])

        self._fmi1Function('TerminateSlave', ['component'], [fmi1Component], fmi1Status)

        self._fmi1Function('ResetSlave', ['component'], [fmi1Component], fmi1Status)

        self._fmi1Function('FreeSlaveInstance', ['component'], [fmi1Component], None)

        self._fmi1Function('SetRealInputDerivatives',
                           ['c', 'vr', 'nvr', 'order', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer), POINTER(fmi1Real)])

        self._fmi1Function('GetRealOutputDerivatives',
                           ['c', 'vr', 'nvr', 'order', 'value'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t, POINTER(fmi1Integer), POINTER(fmi1Real)])

        self._fmi1Function('CancelStep', ['component'], [fmi1Component])

        self._fmi1Function('DoStep',
                           ['component', 'currentCommunicationPoint', 'communicationStepSize', 'newStep'],
                           [fmi1Component, fmi1Real, fmi1Real, fmi1Boolean])

        self._fmi1Function('GetStatus',
                           ['component', 'kind', 'value'],
                           [fmi1Component, fmi1StatusKind, POINTER(fmi1Status)])

        self._fmi1Function('GetRealStatus',
                           ['component', 'kind', 'value'],
                           [fmi1Component, fmi1StatusKind, POINTER(fmi1Real)])

        self._fmi1Function('GetIntegerStatus',
                           ['component', 'kind', 'value'],
                           [fmi1Component, fmi1StatusKind, POINTER(fmi1Integer)])

        self._fmi1Function('GetBooleanStatus',
                           ['component', 'kind', 'value'],
                           [fmi1Component, fmi1StatusKind, POINTER(fmi1Boolean)])

        self._fmi1Function('GetStringStatus',
                           ['component', 'kind', 'value'],
                           [fmi1Component, fmi1StatusKind, POINTER(fmi1String)])

    # Creation and destruction of slave instances and setting debug status

    def instantiate(self, mimeType='application/x-fmu-sharedlibrary', timeout=0, visible=fmi1False,
                    interactive=fmi1False, functions=None, loggingOn=False):

        fmuLocation = pathlib.Path(self.unzipDirectory).as_uri()

        if functions is None:
            functions = fmi1CallbackFunctions()
            functions.logger = fmi1CallbackLoggerTYPE(printLogMessage)
            functions.allocateMemory = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
            functions.freeMemory = fmi1CallbackFreeMemoryTYPE(freeMemory)
            functions.stepFinished = None

        self.callbacks = functions

        self.component = self.fmi1InstantiateSlave(self.instanceName.encode('UTF-8'),
                                                   self.guid.encode('UTF-8'),
                                                   fmuLocation.encode('UTF-8'),
                                                   mimeType.encode('UTF-8'),
                                                   timeout,
                                                   visible,
                                                   interactive,
                                                   functions,
                                                   fmi1True if loggingOn else fmi1False)

    # Inquire version numbers of header files

    def getTypesPlatform(self):
        types_platform = self.fmi1GetTypesPlatform()
        return types_platform.decode('utf-8')

    # Creation and destruction of slave instances and setting debug status

    def initialize(self, tStart=0.0, stopTime=None):
        stopTimeDefined = fmi1True if stopTime is not None else fmi1False
        tStop = stopTime if stopTime is not None else 0.0
        return self.fmi1InitializeSlave(self.component, tStart, stopTimeDefined, tStop)

    def terminate(self):
        return self.fmi1TerminateSlave(self.component)

    def reset(self):
        return self.fmi1ResetSlave(self.component)

    def freeInstance(self):
        self.fmi1FreeSlaveInstance(self.component)
        self.freeLibrary()

    def setRealInputDerivatives(self, vr, order, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        order = (fmi1Integer * len(vr))(*order)
        value = (fmi1Real * len(vr))(*value)
        self.fmi1SetRealInputDerivatives(self.component, vr, len(vr), order, value)

    def getRealOutputDerivatives(self, vr, order):
        vr = (fmi1ValueReference * len(vr))(*vr)
        order = (fmi1Integer * len(vr))(*order)
        value = (fmi1Real * len(vr))()
        self.fmi1GetRealOutputDerivatives(self.component, vr, len(vr), order, value)
        return list(value)

    def cancelStep(self):
        return self.fmi1CancelStep(self.component)

    def doStep(self, currentCommunicationPoint, communicationStepSize, newStep=fmi1True):
        return self.fmi1DoStep(self.component, currentCommunicationPoint, communicationStepSize, newStep)

    def getStatus(self, kind):
        value = fmi1Status(fmi1OK)
        self.fmi1GetStatus(self.component, kind, byref(value))
        return value

    def getRealStatus(self, kind):
        value = fmi1Real(0.0)
        self.fmi1GetRealStatus(self.component, kind, byref(value))
        return value

    def getIntegerStatus(self, kind):
        value = fmi1Integer(0)
        self.fmi1GetIntegerStatus(self.component, kind, byref(value))
        return value

    def getBooleanStatus(self, kind):
        value = fmi1Boolean(fmi1False)
        self.fmi1GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getStringStatus(self, kind):
        value = fmi1String(b'')
        self.fmi1GetStringStatus(self.component, kind, byref(value))
        return value


class FMU1Model(_FMU1):
    """ An FMI 1.0 Model Exchange FMU """

    def __init__(self, **kwargs):

        super(FMU1Model, self).__init__(**kwargs)

        self.eventInfo = fmi1EventInfo()

        # Inquire version numbers of header files
        self._fmi1Function('GetModelTypesPlatform', [], [], fmi1String)

        # Creation and destruction of model instances and setting debug status
        self._fmi1Function('InstantiateModel',
                           ['instanceName', 'guid', 'functions', 'loggingOn'],
                           [fmi1String, fmi1String, fmi1CallbackFunctions, fmi1Boolean],
                           fmi1Component)

        self._fmi1Function('FreeModelInstance', ['component'], [fmi1Component], None)

        # Providing independent variables and re-initialization of caching
        self._fmi1Function('SetTime', ['component', 'time'], [fmi1Component, fmi1Real])

        self._fmi1Function('SetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t])

        self._fmi1Function('CompletedIntegratorStep',
                           ['component', 'callEventUpdate'],
                           [fmi1Component, POINTER(fmi1Boolean)])

        # Evaluation of the model equations
        self._fmi1Function('Initialize',
                           ['component', 'toleranceControlled', 'relativeTolerance', 'eventInfo'],
                           [fmi1Component, fmi1Boolean, fmi1Real, POINTER(fmi1EventInfo)])

        self._fmi1Function('GetDerivatives',
                           ['component', 'derivatives', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t])

        self._fmi1Function('GetEventIndicators',
                           ['component', 'eventIndicators', 'ni'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t])

        self._fmi1Function('EventUpdate',
                           ['component', 'intermediateResults', 'eventInfo'],
                           [fmi1Component, fmi1Boolean, POINTER(fmi1EventInfo)])

        self._fmi1Function('GetContinuousStates',
                           ['component', 'states', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t])

        self._fmi1Function('GetNominalContinuousStates',
                           ['component', 'x_nominal', 'nx'],
                           [fmi1Component, POINTER(fmi1Real), c_size_t])

        self._fmi1Function('GetStateValueReferences',
                           ['component', 'x_nominal', 'nx'],
                           [fmi1Component, POINTER(fmi1ValueReference), c_size_t])

        self._fmi1Function('Terminate', ['component'], [fmi1Component])

    # Inquire version numbers of header files

    def getTypesPlatform(self):
        types_platform = self.fmi1GetModelTypesPlatform()
        return types_platform.decode('utf-8')

    # Creation and destruction of model instances and setting debug status

    def instantiate(self, functions=None, loggingOn=False):

        if functions is None:
            functions = fmi1CallbackFunctions()
            functions.logger = fmi1CallbackLoggerTYPE(printLogMessage)
            functions.allocateMemory = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
            functions.freeMemory = fmi1CallbackFreeMemoryTYPE(freeMemory)
            functions.stepFinished = None

        self.callbacks = functions

        self.component = self.fmi1InstantiateModel(self.instanceName.encode('UTF-8'),
                                                   self.guid.encode('UTF-8'),
                                                   self.callbacks,
                                                   fmi1True if loggingOn else fmi1False)

    def freeInstance(self):
        self.fmi1FreeModelInstance(self.component)
        self.freeLibrary()

    # Providing independent variables and re-initialization of caching

    def setTime(self, time):
        return self.fmi1SetTime(self.component, time)

    def setContinuousStates(self, states, size):
        return self.fmi1SetContinuousStates(self.component, states, size)

    def completedIntegratorStep(self):
        stepEvent = fmi1Boolean()
        self.fmi1CompletedIntegratorStep(self.component, byref(stepEvent))
        return stepEvent != fmi1False

    # Evaluation of the model equations

    def initialize(self, toleranceControlled=fmi1False, relativeTolerance=0.0):
        return self.fmi1Initialize(self.component, toleranceControlled, relativeTolerance, byref(self.eventInfo))

    def getDerivatives(self, derivatives, size):
        return self.fmi1GetDerivatives(self.component, derivatives, size)

    def getEventIndicators(self, eventIndicators, size):
        return self.fmi1GetEventIndicators(self.component, eventIndicators, size)

    def eventUpdate(self, intermediateResults=fmi1False):
        return self.fmi1EventUpdate(self.component, intermediateResults, byref(self.eventInfo))

    def getContinuousStates(self, states, size):
        return self.fmi1GetContinuousStates(self.component, states, size)

    def getNominalContinuousStates(self, x_nominal, size):
        return self.fmi1GetNominalContinuousStates(self.component, x_nominal, size)

    def getStateValueReferences(self, vrx, size):
        return self.fmi1GetStateValueReferences(self.component, vrx, size)

    def terminate(self):
        return self.fmi1Terminate(self.component)
