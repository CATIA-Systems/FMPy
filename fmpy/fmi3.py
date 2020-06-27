""" FMI 3.0 interface """

import os
import pathlib
from ctypes import *
from . import free, calloc, sharedLibraryExtension, platform_tuple
from .fmi1 import _FMU, printLogMessage


fmi3Instance             = c_void_p
fmi3InstanceEnvironment  = c_void_p
fmi3FMUState             = c_void_p
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
fmi3Byte                 = c_char
fmi3Binary               = c_char_p
fmi3Clock                = c_int

# values for fmi3Boolean
fmi3True  = 1
fmi3False = 0

# values for fmi3Clock
fmi3ClockActive   = 1
fmi3ClockInactive = 0

# enum fmi3Status
fmi3Status  = c_int
fmi3OK      = 0
fmi3Warning = 1
fmi3Discard = 2
fmi3Error   = 3
fmi3Fatal   = 4

# enum fmi3DependencyKind
fmi3DependencyKind = c_int
# fmi3Independent = 0, not needed but reserved for future use
fmi3Constant       = 1
fmi3Fixed          = 2
fmi3Tunable        = 3
fmi3Discrete       = 4
fmi3Dependent      = 5

# callback functions
fmi3CallbackLogMessageTYPE         = CFUNCTYPE(None, fmi3InstanceEnvironment, fmi3String, fmi3Status, fmi3String, fmi3String)
fmi3CallbackIntermediateUpdateTYPE = CFUNCTYPE(None, fmi3InstanceEnvironment, fmi3Float64, fmi3Boolean, fmi3Boolean, fmi3Boolean, fmi3Boolean, fmi3Boolean, fmi3Boolean, POINTER(fmi3Boolean), POINTER(fmi3Float64))
fmi3CallbackLockPreemptionTYPE     = CFUNCTYPE(None)
fmi3CallbackUnlockPreemptionTYPE   = CFUNCTYPE(None)


def intermediateUpdate(*args):
    return fmi3OK


def printLogMessage(instanceEnvironment, instanceName, status, category, message):
    """ Print the FMU's log messages to the command line """

    label = ['OK', 'WARNING', 'DISCARD', 'ERROR', 'FATAL', 'PENDING'][status]
    print("[%s] %s" % (label, message))


def stepFinished(instanceEnvironment, status):
    pass


class _FMU3(_FMU):
    """ Base class for FMI 3.0 FMUs """

    def __init__(self, **kwargs):

        # build the path to the shared library
        kwargs['libraryPath'] = os.path.join(kwargs['unzipDirectory'], 'binaries', platform_tuple,
                                             kwargs['modelIdentifier'] + sharedLibraryExtension)

        super(_FMU3, self).__init__(**kwargs)

        # inquire version numbers and setting logging status
        self._fmi3Function('fmi3GetVersion', [], fmi3String)

        self._fmi3Function('fmi3SetDebugLogging', [
            (fmi3Instance,        'instance'),
            (fmi3Boolean,         'loggingOn'),
            (c_size_t,            'nCategories'),
            (POINTER(fmi3String), 'categories')
        ])

        self._fmi3Function('fmi3FreeInstance', [(fmi3Instance, 'instance')], None)

        # Enter and exit initialization mode, terminate and reset
        self._fmi3Function('fmi3EnterInitializationMode', [
            (fmi3Instance, 'instance'),
            (fmi3Boolean,  'toleranceDefined'),
            (fmi3Float64,  'tolerance'),
            (fmi3Float64,  'startTime'),
            (fmi3Boolean,  'stopTimeDefined'),
            (fmi3Float64,  'stopTime')
        ])

        self._fmi3Function('fmi3ExitInitializationMode', [(fmi3Instance, 'instance')])

        self._fmi3Function('fmi3EnterEventMode', [
            (fmi3Instance,       'instance'),
            (fmi3Boolean,        'stepEvent'),
            (POINTER(fmi3Int32), 'rootsFound'),
            (c_size_t,           'nEventIndicators'),
            (fmi3Boolean,        'timeEvent'),
        ])

        self._fmi3Function('fmi3Terminate', [(fmi3Instance, 'instance')])

        self._fmi3Function('fmi3Reset', [(fmi3Instance, 'instance')])

        # Getting and setting variable values
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

        for name, _type in types:

            params = [
                (fmi3Instance,                'instance'),
                (POINTER(fmi3ValueReference), 'vr'),
                (c_size_t,                    'nvr'),
                (POINTER(_type),              'value'),
                (c_size_t,                    'nValues')
            ]

            self._fmi3Function('fmi3Get' + name, params)
            self._fmi3Function('fmi3Set' + name, params)

        self._fmi3Function('fmi3GetBinary', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'vr'),
            (c_size_t,                    'nvr'),
            (POINTER(c_size_t),           'size'),
            (POINTER(fmi3Binary),         'value'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3SetBinary', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'vr'),
            (c_size_t,                    'nvr'),
            (POINTER(c_size_t),           'size'),
            (POINTER(fmi3Binary),         'value'),
            (c_size_t,                    'nValues')
        ])

        # Getting Variable Dependency Information
        self._fmi3Function('fmi3GetNumberOfVariableDependencies', [
            (fmi3Instance,       'instance'),
            (fmi3ValueReference, 'valueReference'),
            (POINTER(c_size_t),  'nDependencies')
        ])

        self._fmi3Function('fmi3GetVariableDependencies', [
            (fmi3Instance,                'instance'),
            (fmi3ValueReference,          'dependent'),
            (POINTER(c_size_t),           'elementIndicesOfDependent'),
            (POINTER(fmi3ValueReference), 'independents'),
            (POINTER(c_size_t),           'elementIndicesOfIndependents'),
            (POINTER(fmi3DependencyKind), 'dependencyKinds'),
            (c_size_t,                    'nDependencies')
        ])

        # Getting and setting the internal FMU state
        self._fmi3Function('fmi3GetFMUState', [(fmi3Instance, 'instance'), (POINTER(fmi3FMUState), 'FMUState')])

        self._fmi3Function('fmi3SetFMUState', [(fmi3Instance, 'instance'), (fmi3FMUState, 'FMUState')])

        self._fmi3Function('fmi3FreeFMUState', [(fmi3Instance, 'instance'), (POINTER(fmi3FMUState), 'FMUState')])

        self._fmi3Function('fmi3SerializedFMUStateSize', [
            (fmi3Instance,      'instance'),
            (fmi3FMUState,      'FMUState'),
            (POINTER(c_size_t), 'size')
        ])

        self._fmi3Function('fmi3SerializeFMUState', [
            (fmi3Instance,      'instance'),
            (fmi3FMUState,      'FMUState'),
            (POINTER(fmi3Byte), 'serializedState'),
            (c_size_t,          'size')
        ])

        self._fmi3Function('fmi3DeSerializeFMUState', [
            (fmi3Instance,          'instance'),
            (POINTER(fmi3Byte),     'serializedState'),
            (c_size_t,              'size'),
            (POINTER(fmi3FMUState), 'FMUState'),
        ])

        # Getting partial derivatives
        self._fmi3Function('fmi3GetDirectionalDerivative', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'unknowns'),
            (c_size_t,                    'nUnknowns'),
            (POINTER(fmi3ValueReference), 'knowns'),
            (c_size_t,                    'nKnowns'),
            (POINTER(fmi3Float64),        'seed'),
            (c_size_t,                    'nSeed'),
            (POINTER(fmi3Float64),        'sensitivity'),
            (c_size_t,                    'nSensitivity')
        ])

        # Entering and exiting the Configuration or Reconfiguration Mode
        self._fmi3Function('fmi3EnterConfigurationMode', [(fmi3Instance, 'instance')])

        self._fmi3Function('fmi3ExitConfigurationMode', [(fmi3Instance, 'instance')])

        # Clock related functions
        self._fmi3Function('fmi3GetClock', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3Clock),          'values'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3SetClock', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3Clock),          'value'),
            (POINTER(fmi3Boolean),        'subactive'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3GetIntervalDecimal', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3Float64),        'interval')
        ])

        self._fmi3Function('fmi3GetIntervalFraction', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3UInt64),         'intervalCounter'),
            (POINTER(fmi3UInt64),         'resolution'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3SetIntervalDecimal', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3Float64),        'interval'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3SetIntervalFraction', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3UInt64),         'intervalCounter'),
            (POINTER(fmi3UInt64),         'resolution'),
            (c_size_t,                    'nValues')
        ])

        self._fmi3Function('fmi3NewDiscreteStates', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Boolean), 'newDiscreteStatesNeeded'),
            (POINTER(fmi3Boolean), 'terminateSimulation'),
            (POINTER(fmi3Boolean), 'nominalsOfContinuousStatesChanged'),
            (POINTER(fmi3Boolean), 'valuesOfContinuousStatesChanged'),
            (POINTER(fmi3Boolean), 'nextEventTimeDefined'),
            (POINTER(fmi3Float64), 'nextEventTime')
        ])

    def _fmi3Function(self, fname, params, restype=fmi3Status):
        """ Add an FMI 3.0 function to this instance and add a wrapper that allows
        logging and checks the return code if the return type is fmi3Status

        Parameters:
            fname     the name of the function
            params    parameters as (type, name) tuples
            restype   return type
        """

        if not hasattr(self.dll, fname):

            def raise_exception(*args):
                raise Exception("Function %s is missing in shared library." % fname)

            setattr(self, fname, raise_exception)

            return

        if len(params) > 0:
            argtypes, argnames = zip(*params)
        else:
            argtypes = argnames = []

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

    def freeInstance(self):
        self.fmi3FreeInstance(self.component)
        self.freeLibrary()

    # Enter and exit initialization mode, terminate and reset

    def enterInitializationMode(self, tolerance=None, startTime=0.0, stopTime=None):

        toleranceDefined = fmi3True if tolerance is not None else fmi3False

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = fmi3True if stopTime is not None else fmi3False

        if stopTime is None:
            stopTime = 0.0

        return self.fmi3EnterInitializationMode(self.component, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)

    def exitInitializationMode(self):
        return self.fmi3ExitInitializationMode(self.component)

    def terminate(self):
        return self.fmi3Terminate(self.component)

    def reset(self):
        return self.fmi3Reset(self.component)

    # Getting and setting variable values

    def getFloat32(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float32 * nValues)()
        self.fmi3GetFloat32(self.component, vr, len(vr), values, nValues)
        return list(values)

    def getFloat64(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float64 * nValues)()
        self.fmi3GetFloat64(self.component, vr, len(vr), values, nValues)
        return list(values)

    def getInt8(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Int8 * nValues)()
        self.fmi3GetInt8(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getUInt8(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3UInt8 * nValues)()
        self.fmi3GetUInt8(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getInt16(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Int16 * nValues)()
        self.fmi3GetInt16(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getUInt16(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3UInt16 * nValues)()
        self.fmi3GetUInt16(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getInt32(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Int32 * nValues)()
        self.fmi3GetInt32(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getUInt32(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3UInt32 * nValues)()
        self.fmi3GetUInt32(self.component, vr, len(vr), value, nValues)
        return list(value)

    def getInt64(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Int64 * nValues)()
        self.fmi3GetInt64(self.component, vr, len(vr), value, nValues)
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

    def getBinary(self, vr):
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Binary * len(vr))()
        size = (c_size_t * len(vr))()
        self.fmi3GetBinary(self.component, vr, len(vr), size, value, len(value))
        return list(value)

    def setFloat32(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float32 * len(values))(*values)
        self.fmi3SetFloat32(self.component, vr, len(vr), values, len(values))

    def setFloat64(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Float64 * len(values))(*values)
        self.fmi3SetFloat64(self.component, vr, len(vr), values, len(values))

    def setInt8(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Int8 * len(values))(*values)
        self.fmi3SetInt8(self.component, vr, len(vr), values, len(values))

    def setUInt8(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3UInt8 * len(values))(*values)
        self.fmi3SetUInt8(self.component, vr, len(vr), values, len(values))

    def setInt16(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Int16 * len(values))(*values)
        self.fmi3SetInt16(self.component, vr, len(vr), values, len(values))

    def setUInt16(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3UInt16 * len(values))(*values)
        self.fmi3SetUInt16(self.component, vr, len(vr), values, len(values))

    def setInt32(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Int32 * len(values))(*values)
        self.fmi3SetInt32(self.component, vr, len(vr), values, len(values))

    def setUInt32(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3UInt32 * len(values))(*values)
        self.fmi3SetUInt32(self.component, vr, len(vr), values, len(values))

    def setInt64(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Int64 * len(values))(*values)
        self.fmi3SetInt64(self.component, vr, len(vr), values, len(values))

    def setUInt64(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3UInt64 * len(values))(*values)
        self.fmi3SetUInt64(self.component, vr, len(vr), values, len(values))

    def setBoolean(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Boolean * len(values))(*values)
        self.fmi3SetBoolean(self.component, vr, len(vr), values, len(values))

    def setString(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = list(map(lambda s: s.encode('utf-8') if s is not None else s, values))
        values = (fmi3String * len(values))(*values)
        self.fmi3SetString(self.component, vr, len(vr), values, len(values))

    def setBinary(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values_ = (fmi3Binary * len(values))(*values)
        size = (c_size_t * len(vr))(*[len(v) for v in values])
        self.fmi3SetBinary(self.component, vr, len(vr), size, values_, len(values))

    # Getting and setting the internal FMU state

    def getFMUState(self):
        state = fmi3FMUState()
        self.fmi3GetFMUState(self.component, byref(state))
        return state

    def setFMUState(self, state):
        self.fmi3SetFMUState(self.component, state)

    def freeFMUState(self, state):
        self.fmi3FreeFMUState(self.component, byref(state))

    def serializeFMUState(self, state):
        """ Serialize an FMU state

        Parameters:
            state   the FMU state

        Returns:
            the serialized state as a byte string
        """

        size = c_size_t()
        self.fmi3SerializedFMUStateSize(self.component, state, byref(size))
        serializedState = create_string_buffer(size.value)
        self.fmi3SerializeFMUState(self.component, state, serializedState, size)
        return serializedState.raw

    def deSerializeFMUState(self, serializedState, state):
        """ De-serialize an FMU state

        Parameters:
            serializedState   the serialized state as a byte string
            state             the FMU state
        """

        buffer = create_string_buffer(serializedState)
        self.fmi3DeSerializeFMUState(self.component, buffer, len(buffer), byref(state))

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

        self._fmi3Function('fmi3InstantiateModelExchange', [
            (fmi3String,                         'instanceName'),
            (fmi3String,                         'instantiationToken'),
            (fmi3String,                         'resourceLocation'),
            (fmi3Boolean,                        'visible'),
            (fmi3Boolean,                        'loggingOn'),
            (fmi3InstanceEnvironment,            'instanceEnvironment'),
            (fmi3CallbackLogMessageTYPE,         'logMessage')
        ], fmi3Instance)

        self._fmi3Function('fmi3EnterContinuousTimeMode', [(fmi3Instance, 'instance')])

        self._fmi3Function('fmi3CompletedIntegratorStep', [
            (fmi3Instance,         'instance'),
            (fmi3Boolean,          'noSetFMUStatePriorToCurrentPoint'),
            (POINTER(fmi3Boolean), 'enterEventMode'),
            (POINTER(fmi3Boolean), 'terminateSimulation')
        ])

        self._fmi3Function('fmi3SetTime', [
            (fmi3Instance, 'instance'),
            (fmi3Float64,  'time')
        ])

        self._fmi3Function('fmi3SetContinuousStates', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Float64), 'continuousStates'),
            (c_size_t,             'nContinuousStates')
        ])

        self._fmi3Function('fmi3GetDerivatives', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Float64), 'derivatives'),
            (c_size_t,             'nContinuousStates')
        ])

        self._fmi3Function('fmi3GetEventIndicators', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Float64), 'eventIndicators'),
            (c_size_t,             'ni')
        ])

        self._fmi3Function('fmi3GetContinuousStates', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Float64), 'continuousStates'),
            (c_size_t,             'nContinuousStates')
        ])

        self._fmi3Function('fmi3GetNominalsOfContinuousStates', [
            (fmi3Instance,         'instance'),
            (POINTER(fmi3Float64), 'nominals'),
            (c_size_t,             'nContinuousStates')
        ])

        self._fmi3Function('fmi3GetNumberOfEventIndicators', [
            (fmi3Instance,      'instance'),
            (POINTER(c_size_t), 'nEventIndicators')
        ])

        self._fmi3Function('fmi3GetNumberOfContinuousStates', [
            (fmi3Instance,      'instance'),
            (POINTER(c_size_t), 'nContinuousStates')
        ])

    def instantiate(self, visible=False, loggingOn=False):

        resourceLocation = pathlib.Path(self.unzipDirectory, 'resources').as_uri()

        # save callbacks from GC
        self.printLogMessage = fmi3CallbackLogMessageTYPE(printLogMessage)

        self.component = self.fmi3InstantiateModelExchange(
            self.instanceName.encode('utf-8'),
            self.guid.encode('utf-8'),
            resourceLocation.encode('utf-8'),
            fmi3True if visible else fmi3False,
            fmi3True if loggingOn else fmi3False,
            fmi3InstanceEnvironment(),
            self.printLogMessage)

        if not self.component:
            raise Exception("Failed to instantiate FMU")

    # Enter and exit the different modes

    def enterEventMode(self, stepEvent=False, rootsFound=[], timeEvent=False):

        rootsFound = (fmi3Int32 * len(rootsFound))(*rootsFound)

        return self.fmi3EnterEventMode(
            self.component,
            fmi3True if stepEvent else fmi3False,
            rootsFound,
            len(rootsFound),
            fmi3True if timeEvent else fmi3False,
        )

    def newDiscreteStates(self):

        newDiscreteStatesNeeded           = fmi3Boolean()
        terminateSimulation               = fmi3Boolean()
        nominalsOfContinuousStatesChanged = fmi3Boolean()
        valuesOfContinuousStatesChanged   = fmi3Boolean()
        nextEventTimeDefined              = fmi3Boolean()
        nextEventTime                     = fmi3Float64()

        self.fmi3NewDiscreteStates(self.component,
                                   byref(newDiscreteStatesNeeded),
                                   byref(terminateSimulation),
                                   byref(nominalsOfContinuousStatesChanged),
                                   byref(valuesOfContinuousStatesChanged),
                                   byref(nextEventTimeDefined),
                                   byref(nextEventTime))

        return (newDiscreteStatesNeeded.value           != fmi3False,
                terminateSimulation.value               != fmi3False,
                nominalsOfContinuousStatesChanged.value != fmi3False,
                valuesOfContinuousStatesChanged.value   != fmi3False,
                nextEventTimeDefined.value              != fmi3False,
                nextEventTime.value)

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

    def setContinuousStates(self, continuousStates, nContinuousStates):
        return self.fmi3SetContinuousStates(self.component, continuousStates, nContinuousStates)

    # Evaluation of the model equations

    def getDerivatives(self, derivatives, nContinuousStates):
        return self.fmi3GetDerivatives(self.component, derivatives, nContinuousStates)

    def getEventIndicators(self, eventIndicators, nEventIndicators):
        return self.fmi3GetEventIndicators(self.component, eventIndicators, nEventIndicators)

    def getContinuousStates(self, continuousStates, nContinuousStates):
        return self.fmi3GetContinuousStates(self.component, continuousStates, nContinuousStates)

    def getNominalsOfContinuousState(self):
        pass


class FMU3Slave(_FMU3):
    """ An FMI 3.0 Co-Simulation FMU """

    def __init__(self, instanceName=None, **kwargs):

        kwargs['instanceName'] = instanceName

        super(FMU3Slave, self).__init__(**kwargs)

        self._fmi3Function('fmi3InstantiateBasicCoSimulation', [
            (fmi3String,                         'instanceName'),
            (fmi3String,                         'instantiationToken'),
            (fmi3String,                         'resourceLocation'),
            (fmi3Boolean,                        'visible'),
            (fmi3Boolean,                        'loggingOn'),
            (fmi3Boolean,                        'intermediateVariableGetRequired'),
            (fmi3Boolean,                        'intermediateInternalVariableGetRequired'),
            (fmi3Boolean,                        'intermediateVariableSetRequired'),
            (fmi3InstanceEnvironment,            'instanceEnvironment'),
            (fmi3CallbackLogMessageTYPE,         'logMessage'),
            (fmi3CallbackIntermediateUpdateTYPE, 'intermediateUpdate')
        ], fmi3Instance)

        # Simulating the slave

        self._fmi3Function('fmi3EnterStepMode', [(fmi3Instance, 'instance')])
        
        self._fmi3Function('fmi3GetOutputDerivatives', [
            (fmi3Instance,                'instance'),
            (POINTER(fmi3ValueReference), 'valueReferences'),
            (c_size_t,                    'nValueReferences'),
            (POINTER(fmi3Int32),          'orders'),
            (POINTER(fmi3Float64),        'values'),
            (c_size_t,                    'nValues'),
        ])

        self._fmi3Function('fmi3DoStep', [
            (fmi3Instance,         'instance'),
            (fmi3Float64,          'currentCommunicationPoint'),
            (fmi3Float64,          'communicationStepSize'),
            (fmi3Boolean,          'noSetFMUStatePriorToCurrentPoint'),
            (POINTER(fmi3Boolean), 'terminate'),
            (POINTER(fmi3Boolean), 'earlyReturn'),
            (POINTER(fmi3Float64), 'lastSuccessfulTime')
        ])

        self._fmi3Function('fmi3ActivateModelPartition', [
            (fmi3Instance,       'instance'),
            (fmi3ValueReference, 'clockReference'),
            (c_size_t,           'clockElementIndex'),
            (fmi3Float64,        'activationTime')
        ])

    def instantiate(self, visible=False, loggingOn=False):

        resourceLocation = pathlib.Path(self.unzipDirectory, 'resources').as_uri()

        # save callbacks from GC
        self.printLogMessage = fmi3CallbackLogMessageTYPE(printLogMessage)
        self.intermediateUpdate = fmi3CallbackIntermediateUpdateTYPE(intermediateUpdate)

        self.component = self.fmi3InstantiateBasicCoSimulation(
            self.instanceName.encode('utf-8'),
            self.guid.encode('utf-8'),
            resourceLocation.encode('utf-8'),
            fmi3True if visible else fmi3False,
            fmi3True if loggingOn else fmi3False,
            fmi3False,
            fmi3False,
            fmi3False,
            fmi3InstanceEnvironment(),
            self.printLogMessage,
            self.intermediateUpdate)

        if not self.component:
            raise Exception("Failed to instantiate FMU")

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
        terminate = fmi3Boolean()
        earlyReturn = fmi3Boolean()
        lastSuccessfulTime = fmi3Float64()
        status = self.fmi3DoStep(self.component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint, byref(terminate), byref(earlyReturn), byref(lastSuccessfulTime))
        return status, terminate.value != fmi3False, earlyReturn.value != fmi3False, lastSuccessfulTime.value

    def cancelStep(self):
        self.fmi3CancelStep(self.component)

    # Inquire slave status

    def getDoStepPendingStatus(self):
        status = fmi3Status(fmi3OK)
        message = fmi3String()
        self.fmi3GetDoStepPendingStatus(self.component, byref(status), byref(message))
        return status, message

    def getDoStepDiscardedStatus(self):
        terminate = fmi3Boolean(fmi3False)
        lastSuccessfulTime = fmi3Float64(0)
        self.fmi3GetDoStepDiscardedStatus(self.component, byref(terminate), byref(lastSuccessfulTime))
        return terminate, lastSuccessfulTime
