""" FMI 3.0 interface """

import os
import pathlib
from ctypes import *
from . import free, calloc
from .fmi1 import _FMU, printLogMessage
from . import architecture, system, sharedLibraryExtension


fmi3Component            = c_void_p
fmi3ComponentEnvironment = c_void_p
fmi3FMUstate             = c_void_p
fmi3ValueReference       = c_uint
fmi3Float32              = c_float
fmi3Float64              = c_double
fmi3Int8                 = c_int8
fmi3UInt8                = c_uint8
fmi3Int16                = c_int16
fmi3UInt16               = c_uint16
fmi3Int32                = c_int32
fmi3UInt32               = c_uint32
fmi3Int64                = c_int64
fmi3UInt64               = c_uint64
fmi3Boolean              = c_int
fmi3Char                 = c_char
fmi3String               = c_char_p
fmi3Type                 = c_int
fmi3Byte                 = c_char

fmi3Status = c_int

fmi3OK      = 0
fmi3Warning = 1
fmi3Discard = 2
fmi3Error   = 3
fmi3Fatal   = 4
fmi3Pending = 5

fmi3CallbackLoggerTYPE         = CFUNCTYPE(None, fmi3ComponentEnvironment, fmi3String, fmi3Status, fmi3String, fmi3String)
fmi3CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, fmi3ComponentEnvironment, c_size_t, c_size_t)
fmi3CallbackFreeMemoryTYPE     = CFUNCTYPE(None, fmi3ComponentEnvironment, c_void_p)
fmi3StepFinishedTYPE           = CFUNCTYPE(None, fmi3ComponentEnvironment, fmi3Status)

fmi3ModelExchange = 0
fmi3CoSimulation  = 1

fmi3True  = 1
fmi3False = 0

# allocated memory
_mem_addr = set()


def printLogMessage(componentEnvironment, instanceName, status, category, message):
    """ Print the FMU's log messages to the command line """

    label = ['OK', 'WARNING', 'DISCARD', 'ERROR', 'FATAL', 'PENDING'][status]
    print("[%s] %s" % (label, message))


def allocateMemory(componentEnvironment, nobj, size):
    mem = calloc(nobj, size)
    _mem_addr.add(mem)
    return mem


def freeMemory(componentEnvironment, obj):
    if obj in _mem_addr:
        free(obj)
        _mem_addr.remove(obj)
    else:
        print("freeMemory() was called for a pointer (%s) that was not allocated" % obj)


def stepFinished(componentEnvironment, status):
    pass


class fmi3CallbackFunctions(Structure):

    _fields_ = [('logger',               fmi3CallbackLoggerTYPE),
                ('allocateMemory',       fmi3CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi3CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi3StepFinishedTYPE),
                ('componentEnvironment', fmi3ComponentEnvironment)]


class fmi3EventInfo(Structure):

    _fields_ = [('newDiscreteStatesNeeded',           fmi3Boolean),
                ('terminateSimulation',               fmi3Boolean),
                ('nominalsOfContinuousStatesChanged', fmi3Boolean),
                ('valuesOfContinuousStatesChanged',   fmi3Boolean),
                ('nextEventTimeDefined',              fmi3Boolean),
                ('nextEventTime',                     fmi3Float64)]


class _FMU3(_FMU):
    """ Base class for FMI 3.0 FMUs """

    def __init__(self, **kwargs):

        # build the path to the shared library
        kwargs['libraryPath'] = os.path.join(kwargs['unzipDirectory'], 'binaries', architecture + '-' + system,
                                             kwargs['modelIdentifier'] + sharedLibraryExtension)

        super(_FMU3, self).__init__(**kwargs)

        # Inquire version numbers of header files and setting logging status
        self._fmi3Function('fmi3GetTypesPlatform', [], [], fmi3String)

        self._fmi3Function('fmi3GetVersion', [], [], fmi3String)

        self._fmi3Function('fmi3SetDebugLogging',
                           ['component', 'loggingOn', 'nCategories', 'categories'],
                           [fmi3Component, fmi3Boolean, c_size_t, POINTER(fmi3String)])

        # Creation and destruction of FMU instances and setting debug status
        self._fmi3Function('fmi3Instantiate',
                           ['instanceName', 'fmuType', 'guid', 'resourceLocation', 'callbacks', 'visible', 'loggingOn'],
                           [fmi3String, fmi3Type, fmi3String, fmi3String, POINTER(fmi3CallbackFunctions), fmi3Boolean, fmi3Boolean],
                           fmi3Component)

        self._fmi3Function('fmi3FreeInstance', ['component'], [fmi3Component], None)

        # Enter and exit initialization mode, terminate and reset
        self._fmi3Function('fmi3SetupExperiment',
                           ['component', 'toleranceDefined', 'tolerance', 'startTime', 'stopTimeDefined', 'stopTime'],
                           [fmi3Component, fmi3Boolean, fmi3Float64, fmi3Float64, fmi3Boolean, fmi3Float64])

        self._fmi3Function('fmi3EnterInitializationMode', ['component'], [fmi3Component], fmi3Status)

        self._fmi3Function('fmi3ExitInitializationMode', ['component'], [fmi3Component], fmi3Status)

        self._fmi3Function('fmi3Terminate', ['component'], [fmi3Component], fmi3Status)

        self._fmi3Function('fmi3Reset', ['component'], [fmi3Component], fmi3Status)

        types = [
            ('Float32', fmi3Float32),
            ('Float64', fmi3Float64),
            ('Int8',    fmi3Int8),
            ('UInt8',   fmi3UInt8),
            ('Int16',   fmi3Int16),
            ('UInt16',  fmi3UInt16),
            ('Int32',   fmi3Int32),
            ('UInt32',  fmi3UInt32),
            ('Int64',   fmi3Int64),
            ('UInt64',  fmi3UInt64),
            ('Boolean', fmi3Boolean),
            ('String',  fmi3String),
        ]

        # Getting and setting variable values
        for name, _type in types:

            self._fmi3Function('fmi3Get' + name,
                               ['component', 'vr', 'nvr', 'value', 'nValues'],
                               [fmi3Component, POINTER(fmi3ValueReference), c_size_t, POINTER(_type), c_size_t])

            self._fmi3Function('fmi3Set' + name,
                               ['component', 'vr', 'nvr', 'value', 'nValues'],
                               [fmi3Component, POINTER(fmi3ValueReference), c_size_t, POINTER(_type), c_size_t])

        # Getting and setting the internal FMU state
        self._fmi3Function('fmi3GetFMUstate', ['component', 'FMUstate'],
                           [fmi3Component, POINTER(fmi3FMUstate)])

        self._fmi3Function('fmi3SetFMUstate', ['component', 'FMUstate'],
                           [fmi3Component, fmi3FMUstate])

        self._fmi3Function('fmi3FreeFMUstate', ['component', 'FMUstate'],
                           [fmi3Component, POINTER(fmi3FMUstate)])

        self._fmi3Function('fmi3SerializedFMUstateSize',
                           ['component', 'FMUstate', 'size'],
                           [fmi3Component, fmi3FMUstate, POINTER(c_size_t)])

        self._fmi3Function('fmi3SerializeFMUstate',
                           ['component', 'FMUstate', 'serializedState', 'size'],
                           [fmi3Component, fmi3FMUstate, POINTER(fmi3Byte), c_size_t])

        self._fmi3Function('fmi3DeSerializeFMUstate',
                           ['component', 'FMUstate', 'serializedState', 'size'],
                           [fmi3Component, POINTER(fmi3Byte), c_size_t, POINTER(fmi3FMUstate)])

        # Getting partial derivatives
        self._fmi3Function('fmi3GetDirectionalDerivative',
                           ['component', 'vUnknown_ref', 'nUnknown', 'vKnown_ref', 'nKnown', 'dvKnown', 'dvUnknown'],
                           [fmi3Component, POINTER(fmi3ValueReference), c_size_t, POINTER(fmi3ValueReference), c_size_t, POINTER(fmi3Float64), POINTER(fmi3Float64)])

    def _fmi3Function(self, fname, argnames, argtypes, restype=fmi3Status):
        """ Add an FMI 3.0 function to this instance and add a wrapper that allows
        logging and checks the return code if the return type is fmi3Status

        Parameters:
            fname     the name of the function
            argnames  names of the arguments
            argtypes  types of the arguments
            restype   return type
        """

        if not hasattr(self.dll, fname):
            setattr(self, fname, None)
            return

        # get the exported function form the shared library
        f = getattr(self.dll, fname)
        f.argtypes = argtypes
        f.restype = restype

        def w(*args):
            """ Wrapper function for the FMI call """

            # call the FMI function
            res = f(*args)

            if self.fmiCallLogger is not None:
                # log the call
                self._log_fmi_args(fname, argnames, argtypes, args, restype, res)

            if restype == fmi3Status:  # status code
                # check the status code
                if res > fmi3Warning:
                    raise Exception("%s failed with status %d." % (fname, res))

            return res

        setattr(self, fname, w)

    # Inquire version numbers of header files and setting logging status

    def getVersion(self):
        version = self.fmi3GetVersion()
        return version.decode('utf-8')

    def setDebugLogging(self, loggingOn, categories):
        categories_ = (fmi3String * len(categories))()
        categories_[:] = [c.encode('utf-8') for c in categories]
        self.fmi3SetDebugLogging(self.component, fmi3True if loggingOn else fmi3False, len(categories), categories_)

    # Creation and destruction of FMU instances and setting debug status

    def instantiate(self, visible=False, callbacks=None, loggingOn=False):

        kind = fmi3ModelExchange if isinstance(self, FMU3Model) else fmi3CoSimulation
        resourceLocation = pathlib.Path(self.unzipDirectory, 'resources').as_uri()

        if callbacks is None:
            callbacks = fmi3CallbackFunctions()
            callbacks.logger = fmi3CallbackLoggerTYPE(printLogMessage)
            callbacks.reallocateMemory = fmi3CallbackReallocateMemoryTYPE(reallocateMemory)
            callbacks.freeMemory = fmi3CallbackFreeMemoryTYPE(freeMemory)

        self.callbacks = callbacks

        self.component = self.fmi3Instantiate(self.instanceName.encode('utf-8'),
                                              kind,
                                              self.guid.encode('utf-8'),
                                              resourceLocation.encode('utf-8'),
                                              byref(self.callbacks),
                                              fmi3True if visible else fmi3False,
                                              fmi3True if loggingOn else fmi3False)

    def freeInstance(self):
        self.fmi3FreeInstance(self.component)
        self.freeLibrary()

    # Enter and exit initialization mode, terminate and reset

    def setupExperiment(self, tolerance=None, startTime=0.0, stopTime=None):

        toleranceDefined = fmi3True if tolerance is not None else fmi3False

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = fmi3True if stopTime is not None else fmi3False

        if stopTime is None:
            stopTime = 0.0

        return self.fmi3SetupExperiment(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)

    def enterInitializationMode(self):
        return self.fmi3EnterInitializationMode(self.component)

    def exitInitializationMode(self):
        return self.fmi3ExitInitializationMode(self.component)

    def terminate(self):
        return self.fmi3Terminate(self.component)

    def reset(self):
        return self.fmi3Reset(self.component)

    # Getting and setting variable values

    def getFloat64(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float64 * nValues)()
        self.fmi3GetFloat64(self.component, vr, len(vr), values, nValues)
        return list(values)

    def getInt32(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Int32 * nValues)()
        self.fmi3GetInt32(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getUInt64(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3UInt64 * nValues)()
        self.fmi3GetUInt64(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getBoolean(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Boolean * nValues)()
        self.fmi3GetBoolean(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getString(self, vr):
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3String * len(vr))()
        self.fmi3GetString(self.component, vr, len(vr), value)
        return list(value)

    def setFloat64(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float64 * len(values))(*values)
        self.fmi3SetFloat64(self.component, vr, len(vr), values, len(values))

    def setInt32(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Int32 * len(values))(*values)
        self.fmi3SetInt32(self.component, vr, len(vr), values, len(values))

    def setBoolean(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Boolean * len(values))(*values)
        self.fmi3SetBoolean(self.component, vr, len(vr), values, len(values))

    def setString(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = list(map(lambda s: s.encode('utf-8') if s is not None else s, values))
        values = (fmi3String * len(values))(*values)
        self.fmi3SetString(self.component, vr, len(vr), values, len(values))

    # Getting and setting the internal FMU state

    def getFMUstate(self):
        state = fmi3FMUstate()
        self.fmi3GetFMUstate(self.component, byref(state))
        return state

    def setFMUstate(self, state):
        self.fmi3SetFMUstate(self.component, state)

    def freeFMUstate(self, state):
        self.fmi3FreeFMUstate(self.component, byref(state))

    def serializeFMUstate(self, state):
        """ Serialize an FMU state

        Parameters:
            state   the FMU state

        Returns:
            the serialized state as a byte string
        """

        size = c_size_t()
        self.fmi3SerializedFMUstateSize(self.component, state, byref(size))
        serializedState = create_string_buffer(size.value)
        self.fmi3SerializeFMUstate(self.component, state, serializedState, size)
        return serializedState.raw

    def deSerializeFMUstate(self, serializedState, state):
        """ De-serialize an FMU state

        Parameters:
            serializedState   the serialized state as a byte string
            state             the FMU state
        """

        buffer = create_string_buffer(serializedState)
        self.fmi3DeSerializeFMUstate(self.component, buffer, len(buffer), byref(state))

    # Getting partial derivatives

    def getDirectionalDerivative(self, vUnknown_ref, vKnown_ref, dvKnown):
        """ Get partial derivatives

        Parameters:
            vUnknown_ref    a list of value references of the unknowns
            vKnown_ref      a list of value references of the knowns
            dvKnown         a list of delta values (one per known)

        Returns:
            a list of the partial derivatives (one per unknown)
        """

        vUnknown_ref = (fmi3ValueReference * len(vUnknown_ref))(*vUnknown_ref)
        vKnown_ref = (fmi3ValueReference * len(vKnown_ref))(*vKnown_ref)
        dvKnown = (fmi3Float64 * len(dvKnown))(*dvKnown)
        dvUnknown = (fmi3Float64 * len(vUnknown_ref))()

        self.fmi3GetDirectionalDerivative(self.component, vUnknown_ref, len(vUnknown_ref), vKnown_ref, len(vKnown_ref), dvKnown, dvUnknown)

        return list(dvUnknown)


class FMU3Model(_FMU3):
    """ An FMI 3.0 Model Exchange FMU """

    def __init__(self, **kwargs):

        super(FMU3Model, self).__init__(**kwargs)

        self.eventInfo = fmi3EventInfo()

        self._fmi3Function('fmi3NewDiscreteStates',
                           ['component', 'eventInfo'],
                           [fmi3Component, POINTER(fmi3EventInfo)])

        self._fmi3Function('fmi3EnterContinuousTimeMode',
                           ['component'],
                           [fmi3Component])

        self._fmi3Function('fmi3EnterEventMode',
                           ['component'],
                           [fmi3Component])

        self._fmi3Function('fmi3GetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi3Component, POINTER(fmi3Float64), c_size_t])

        self._fmi3Function('fmi3SetContinuousStates',
                           ['component', 'x', 'nx'],
                           [fmi3Component, POINTER(fmi3Float64), c_size_t])

        self._fmi3Function('fmi3GetDerivatives',
                           ['component', 'derivatives', 'nx'],
                           [fmi3Component, POINTER(fmi3Float64), c_size_t])

        self._fmi3Function('fmi3GetEventIndicators',
                           ['component', 'eventIndicators', 'ni'],
                           [fmi3Component, POINTER(fmi3Float64), c_size_t])

        self._fmi3Function('fmi3SetTime',
                           ['component', 'time'],
                           [fmi3Component, fmi3Float64])

        self._fmi3Function('fmi3CompletedIntegratorStep',
                           ['component', 'noSetFMUStatePriorToCurrentPoint', 'enterEventMode', 'terminateSimulation'],
                           [fmi3Component, fmi3Boolean, POINTER(fmi3Boolean), POINTER(fmi3Boolean)])

    # Enter and exit the different modes

    def enterEventMode(self):
        return self.fmi3EnterEventMode(self.component)

    def newDiscreteStates(self):
        return self.fmi3NewDiscreteStates(self.component, byref(self.eventInfo))

    def enterContinuousTimeMode(self):
        return self.fmi3EnterContinuousTimeMode(self.component)

    def completedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint=fmi3True):
        enterEventMode = fmi3Boolean()
        terminateSimulation = fmi3Boolean()
        self.fmi3CompletedIntegratorStep(self.component, noSetFMUStatePriorToCurrentPoint, byref(enterEventMode), byref(terminateSimulation))
        return enterEventMode.value, terminateSimulation.value

    # Providing independent variables and re-initialization of caching

    def setTime(self, time):
        return self.fmi3SetTime(self.component, time)

    def setContinuousStates(self, x, nx):
        return self.fmi3SetContinuousStates(self.component, x, nx)

    # Evaluation of the model equations

    def getDerivatives(self, dx, nx):
        return self.fmi3GetDerivatives(self.component, dx, nx)

    def getEventIndicators(self, z, nz):
        return self.fmi3GetEventIndicators(self.component, z, nz)

    def getContinuousStates(self, x, nx):
        return self.fmi3GetContinuousStates(self.component, x, nx)

    def getNominalsOfContinuousStatesTYPE(self):
        pass


class FMU3Slave(_FMU3):
    """ An FMI 3.0 Co-Simulation FMU """

    def __init__(self, instanceName=None, **kwargs):

        kwargs['instanceName'] = instanceName

        super(FMU3Slave, self).__init__(**kwargs)

        # Simulating the slave

        self._fmi3Function('fmi3SetInputDerivatives',
                           ['component', 'vr', 'nvr', 'order', 'value'],
                           [fmi3Component, POINTER(fmi3ValueReference), c_size_t, POINTER(fmi3Int32), POINTER(fmi3Float64)])

        self._fmi3Function('fmi3GetOutputDerivatives',
                           ['component', 'vr', 'nvr', 'order', 'value'],
                           [fmi3Component, POINTER(fmi3ValueReference), c_size_t, POINTER(fmi3Int32), POINTER(fmi3Float64)])

        self._fmi3Function('fmi3DoStep',
                           ['component', 'currentCommunicationPoint', 'communicationStepSize', 'noSetFMUStatePriorToCurrentPoint'],
                           [fmi3Component, fmi3Float64, fmi3Float64, fmi3Boolean])

        self._fmi3Function('fmi3CancelStep', ['component'], [fmi3Component])

        # Inquire slave status

        self._fmi3Function('fmi3GetDoStepPendingStatus',
                           ['component', 'status', 'message'],
                           [fmi3Component, POINTER(fmi3Status), POINTER(fmi3String)])

        self._fmi3Function('fmi3GetDoStepDiscardedStatus',
                           ['component', 'terminate', 'lastSuccessfulTime'],
                           [fmi3Component, POINTER(fmi3Boolean), POINTER(fmi3Float64)])

    # Simulating the slave

    def setInputDerivatives(self, vr, order, value):
        vr = (fmi3ValueReference * len(vr))(*vr)
        order = (fmi3Int32 * len(vr))(*order)
        value = (fmi3Float64 * len(vr))(*value)
        self.fmi3SetInputDerivatives(self.component, vr, len(vr), order, value)

    def getOutputDerivatives(self, vr, order):
        vr = (fmi3ValueReference * len(vr))(*vr)
        order = (fmi3Int32 * len(vr))(*order)
        value = (fmi3Float64 * len(vr))()
        self.fmi3GetOutputDerivatives(self.component, vr, len(vr), order, value)
        return list(value)

    def doStep(self, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint=fmi3True):
        return self.fmi3DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)

    def cancelStep(self):
        self.fmi3CancelStep(self.component)

    # Inquire slave status

    def getStatus(self, kind):
        value = fmi3Status(fmi3OK)
        self.fmi3GetStatus(self.component, kind, byref(value))
        return value

    def getRealStatus(self, kind):
        value = fmi3Float64(0.0)
        self.fmi3GetRealStatus(self.component, kind, byref(value))
        return value

    def getIntegerStatus(self, kind):
        value = fmi3Int32(0)
        self.fmi3GetIntegerStatus(self.component, kind, byref(value))
        return value

    def getBooleanStatus(self, kind):
        value = fmi3Boolean(fmi3False)
        self.fmi3GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getStringStatus(self, kind):
        value = fmi3String(b'')
        self.fmi3GetStringStatus(self.component, kind, byref(value))
        return value
