"""FMI 3.0 interface"""

from ctypes import (
    c_void_p,
    c_uint,
    c_double,
    c_int,
    c_char,
    c_char_p,
    byref,
    c_size_t,
    POINTER,
    cast,
    c_bool,
    c_float,
    c_int8,
    c_int16,
    c_int32,
    c_int64,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    CFUNCTYPE,
    create_string_buffer,
)

import os
from typing import Tuple, Sequence, List, Iterable

from . import sharedLibraryExtension, platform_tuple
from .fmi1 import _FMU

fmi3Instance = c_void_p
fmi3InstanceEnvironment = c_void_p
fmi3FMUState = c_void_p
fmi3ValueReference = c_uint
fmi3Float32 = c_float
fmi3Float64 = c_double
fmi3Int8 = c_int8
fmi3UInt8 = c_uint8
fmi3Int16 = c_int16
fmi3UInt16 = c_uint16
fmi3Int32 = c_int32
fmi3UInt32 = c_uint32
fmi3Int64 = c_int64
fmi3UInt64 = c_uint64
fmi3Boolean = c_bool
fmi3Char = c_char
fmi3String = c_char_p
fmi3Byte = c_uint8
fmi3Binary = POINTER(fmi3Byte)
fmi3Clock = c_bool

# values for fmi3Boolean
fmi3True = c_bool(True)
fmi3False = c_bool(False)

# values for fmi3Clock
fmi3ClockActive = c_bool(True)
fmi3ClockInactive = c_bool(False)

# enum fmi3Status
fmi3Status = c_int
fmi3OK = 0
fmi3Warning = 1
fmi3Discard = 2
fmi3Error = 3
fmi3Fatal = 4

# enum fmi3DependencyKind
fmi3DependencyKind = c_int
fmi3Independent = 0
fmi3Constant = 1
fmi3Fixed = 2
fmi3Tunable = 3
fmi3Discrete = 4
fmi3Dependent = 5

# enum fmi3IntervalQualifier
fmi3IntervalQualifier = c_int
fmi3IntervalNotYetKnown = 0
fmi3IntervalUnchanged = 1
fmi3IntervalChanged = 2

# callback functions
fmi3LogMessageCallback = CFUNCTYPE(
    None, fmi3InstanceEnvironment, fmi3Status, fmi3String, fmi3String
)
fmi3ClockUpdateCallback = CFUNCTYPE(None, fmi3InstanceEnvironment)
fmi3IntermediateUpdateCallback = CFUNCTYPE(
    None,
    fmi3InstanceEnvironment,
    fmi3Float64,
    fmi3Boolean,
    fmi3Boolean,
    fmi3Boolean,
    fmi3Boolean,
    POINTER(fmi3Boolean),
    POINTER(fmi3Float64),
)
fmi3LockPreemptionCallback = CFUNCTYPE(None)
fmi3UnlockPreemptionCallback = CFUNCTYPE(None)


def printLogMessage(
    instanceEnvironment: fmi3InstanceEnvironment,
    status: fmi3Status,
    category: fmi3String | bytes,
    message: fmi3String | bytes,
) -> None:
    """Print the FMU's log messages to the command line"""

    label = ["OK", "WARNING", "DISCARD", "ERROR", "FATAL", "PENDING"][status]
    print(f"[{label}] {message.decode('utf-8')}")


class _FMU3(_FMU):
    """Base class for FMI 3.0 FMUs"""

    def __init__(self, **kwargs):
        # build the path to the shared library
        kwargs["libraryPath"] = os.path.join(
            kwargs["unzipDirectory"],
            "binaries",
            platform_tuple,
            kwargs["modelIdentifier"] + sharedLibraryExtension,
        )

        super(_FMU3, self).__init__(**kwargs)

    # inquire version numbers and setting logging status

    def fmi3GetVersion(self) -> bytes:
        return self._call("fmi3GetVersion")

    def fmi3SetDebugLogging(
        self,
        instance: fmi3Instance,
        loggingOn: fmi3Boolean | bool,
        nCategories: c_size_t | int,
        categories: POINTER(fmi3String),
    ) -> int:
        return self._call(
            "fmi3SetDebugLogging",
            instance,
            loggingOn,
            nCategories,
            categories,
        )

    def fmi3InstantiateModelExchange(
        self,
        instanceName: fmi3String | bytes,
        instantiationToken: fmi3String | bytes,
        resourcePath: fmi3String | bytes,
        visible: fmi3Boolean | bool,
        loggingOn: fmi3Boolean | bool,
        instanceEnvironment: fmi3InstanceEnvironment,
        logMessage: fmi3LogMessageCallback,
    ) -> fmi3Instance:
        return self._call(
            "fmi3InstantiateModelExchange",
            instanceName,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            instanceEnvironment,
            logMessage,
        )

    def fmi3InstantiateCoSimulation(
        self,
        instanceName: fmi3String | bytes,
        instantiationToken: fmi3String | bytes,
        resourcePath: fmi3String | bytes,
        visible: fmi3Boolean | bool,
        loggingOn: fmi3Boolean | bool,
        eventModeUsed: fmi3Boolean | bool,
        earlyReturnAllowed: fmi3Boolean | bool,
        requiredIntermediateVariables: POINTER(fmi3ValueReference),
        nRequiredIntermediateVariables: c_size_t | int,
        instanceEnvironment: fmi3InstanceEnvironment,
        logMessage: fmi3LogMessageCallback,
        intermediateUpdat: fmi3IntermediateUpdateCallback,
    ) -> fmi3Instance:
        return self._call(
            "fmi3InstantiateCoSimulation",
            instanceName,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            eventModeUsed,
            earlyReturnAllowed,
            requiredIntermediateVariables,
            nRequiredIntermediateVariables,
            instanceEnvironment,
            logMessage,
            intermediateUpdat,
        )

    def fmi3InstantiateScheduledExecution(
        self,
        instanceName: fmi3String | bytes,
        instantiationToken: fmi3String | bytes,
        resourcePath: fmi3String | bytes,
        visible: fmi3Boolean | bool,
        loggingOn: fmi3Boolean | bool,
        instanceEnvironment: fmi3InstanceEnvironment,
        logMessage: fmi3LogMessageCallback,
        clockUpdate: fmi3ClockUpdateCallback,
        lockPreemption: fmi3LockPreemptionCallback,
        unlockPreemption: fmi3UnlockPreemptionCallback,
    ) -> fmi3Instance:
        return self._call(
            "fmi3InstantiateScheduledExecution",
            instanceName,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            instanceEnvironment,
            logMessage,
            clockUpdate,
            lockPreemption,
            unlockPreemption,
        )

    def fmi3FreeInstance(self, instance: fmi3Instance) -> None:
        self._call("fmi3FreeInstance", instance)

    def fmi3EnterInitializationMode(
        self,
        instance: fmi3Instance,
        toleranceDefined: fmi3Boolean | bool,
        tolerance: fmi3Float64 | float,
        startTime: fmi3Float64 | float,
        stopTimeDefined: fmi3Boolean | bool,
        stopTime: fmi3Float64 | float,
    ) -> int:
        return self._call(
            "fmi3EnterInitializationMode",
            instance,
            toleranceDefined,
            tolerance,
            startTime,
            stopTimeDefined,
            stopTime,
        )

    def fmi3ExitInitializationMode(self, instance: fmi3Instance) -> int:
        return self._call("fmi3ExitInitializationMode", instance)

    def fmi3EnterEventMode(self, instance: fmi3Instance) -> int:
        return self._call("fmi3EnterEventMode", instance)

    def fmi3Terminate(self, instance: fmi3Instance) -> int:
        return self._call("fmi3Terminate", instance)

    def fmi3Reset(self, instance: fmi3Instance) -> int:
        return self._call("fmi3Reset", instance)

    def fmi3GetFloat32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Float32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetFloat32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    # Getting and setting variable values

    def fmi3GetFloat64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Float64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetFloat64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetInt8(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int8),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetInt8",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetUInt8(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt8),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetUInt8",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetInt16(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int16),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetInt16",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetUInt16(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt16),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetUInt16",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetInt32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetInt32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetUInt32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetUInt32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetInt64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetInt64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetUInt64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetUInt64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetBoolean(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Boolean),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetBoolean",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetString(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3String),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetString",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3GetBinary(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        valueSizes: POINTER(c_size_t),
        values: POINTER(fmi3Binary),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetBinary",
            instance,
            valueReferences,
            nValueReferences,
            valueSizes,
            values,
            nValues,
        )

    def fmi3GetClock(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Clock),
    ) -> int:
        return self._call(
            "fmi3GetClock",
            instance,
            valueReferences,
            nValueReferences,
            values,
        )

    def fmi3SetFloat32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Float32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetFloat32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetFloat64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Float64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetFloat64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetInt8(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int8),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetInt8",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetUInt8(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt8),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetUInt8",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetInt16(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int16),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetInt16",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetUInt16(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt16),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetUInt16",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetInt32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetInt32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetUInt32(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt32),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetUInt32",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetInt64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Int64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetInt64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetUInt64(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3UInt64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetUInt64",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetBoolean(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Boolean),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetBoolean",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetString(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3String),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetString",
            instance,
            valueReferences,
            nValueReferences,
            values,
            nValues,
        )

    def fmi3SetBinary(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        valueSizes: POINTER(c_size_t),
        values: POINTER(fmi3Binary),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetBinary",
            instance,
            valueReferences,
            nValueReferences,
            valueSizes,
            values,
            nValues,
        )

    def fmi3SetClock(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        values: POINTER(fmi3Clock),
    ) -> int:
        return self._call(
            "fmi3SetClock",
            instance,
            valueReferences,
            nValueReferences,
            values,
        )

    # Getting Variable Dependency Information

    def fmi3GetNumberOfVariableDependencies(
        self,
        instance: fmi3Instance,
        valueReference: fmi3ValueReference,
        nDependencies: POINTER(c_size_t),
    ) -> int:
        return self._call(
            "fmi3GetNumberOfVariableDependencies",
            instance,
            valueReference,
            nDependencies,
        )

    def fmi3GetVariableDependencies(
        self,
        instance: fmi3Instance,
        dependent: fmi3ValueReference,
        elementIndicesOfDependent: POINTER(c_size_t),
        independents: POINTER(fmi3ValueReference),
        elementIndicesOfIndependents: POINTER(c_size_t),
        dependencyKinds: POINTER(fmi3DependencyKind),
        nDependencies: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetVariableDependencies",
            instance,
            dependent,
            elementIndicesOfDependent,
            independents,
            elementIndicesOfIndependents,
            dependencyKinds,
            nDependencies,
        )

    # Getting and setting the internal FMU state

    def fmi3GetFMUState(
        self,
        instance: fmi3Instance,
        FMUState: POINTER(fmi3FMUState),
    ) -> int:
        return self._call(
            "fmi3GetFMUState",
            instance,
            FMUState,
        )

    def fmi3SetFMUState(
        self,
        instance: fmi3Instance,
        FMUState: fmi3FMUState,
    ) -> int:
        return self._call(
            "fmi3SetFMUState",
            instance,
            FMUState,
        )

    def fmi3FreeFMUState(
        self,
        instance: fmi3Instance,
        FMUState: POINTER(fmi3FMUState),
    ) -> int:
        return self._call(
            "fmi3FreeFMUState",
            instance,
            FMUState,
        )

    def fmi3SerializedFMUStateSize(
        self,
        instance: fmi3Instance,
        FMUState: fmi3FMUState,
        size: POINTER(c_size_t),
    ) -> int:
        return self._call(
            "fmi3SerializedFMUStateSize",
            instance,
            FMUState,
            size,
        )

    def fmi3SerializeFMUState(
        self,
        instance: fmi3Instance,
        FMUState: fmi3FMUState,
        serializedState: POINTER(fmi3Byte),
        size: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SerializeFMUState",
            instance,
            FMUState,
            serializedState,
            size,
        )

    def fmi3DeserializeFMUState(
        self,
        instance: fmi3Instance,
        serializedState: POINTER(fmi3Byte),
        size: c_size_t | int,
        FMUState: POINTER(fmi3FMUState),
    ) -> int:
        return self._call(
            "fmi3DeserializeFMUState",
            instance,
            serializedState,
            size,
            FMUState,
        )

    # Getting partial derivatives

    def fmi3GetDirectionalDerivative(
        self,
        instance: fmi3Instance,
        unknowns: POINTER(fmi3ValueReference),
        nUnknowns: c_size_t | int,
        knowns: POINTER(fmi3ValueReference),
        nKnowns: c_size_t | int,
        seed: POINTER(fmi3Float64),
        nSeed: c_size_t | int,
        sensitivity: POINTER(fmi3Float64),
        nSensitivity: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetDirectionalDerivative",
            instance,
            unknowns,
            nUnknowns,
            knowns,
            nKnowns,
            seed,
            nSeed,
            sensitivity,
            nSensitivity,
        )

    def fmi3GetAdjointDerivative(
        self,
        instance: fmi3Instance,
        unknowns: POINTER(fmi3ValueReference),
        nUnknowns: c_size_t | int,
        knowns: POINTER(fmi3ValueReference),
        nKnowns: c_size_t | int,
        seed: POINTER(fmi3Float64),
        nSeed: c_size_t | int,
        sensitivity: POINTER(fmi3Float64),
        nSensitivity: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetAdjointDerivative",
            instance,
            unknowns,
            nUnknowns,
            knowns,
            nKnowns,
            seed,
            nSeed,
            sensitivity,
            nSensitivity,
        )

    # Entering and exiting the Configuration or Reconfiguration Mode

    def fmi3EnterConfigurationMode(
        self,
        instance: fmi3Instance,
    ) -> int:
        return self._call(
            "fmi3EnterConfigurationMode",
            instance,
        )

    def fmi3ExitConfigurationMode(
        self,
        instance: fmi3Instance,
    ) -> int:
        return self._call(
            "fmi3ExitConfigurationMode",
            instance,
        )

    # Clock related functions

    def fmi3GetIntervalDecimal(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        intervals: POINTER(fmi3Float64),
        qualifiers: POINTER(fmi3IntervalQualifier),
    ) -> int:
        return self._call(
            "fmi3GetIntervalDecimal",
            instance,
            valueReferences,
            nValueReferences,
            intervals,
            qualifiers,
        )

    def fmi3GetIntervalFraction(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        counters: POINTER(fmi3UInt64),
        resolutions: POINTER(fmi3UInt64),
        qualifiers: POINTER(fmi3IntervalQualifier),
    ) -> int:
        return self._call(
            "fmi3GetIntervalFraction",
            instance,
            valueReferences,
            nValueReferences,
            counters,
            resolutions,
            qualifiers,
        )

    def fmi3GetShiftDecimal(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        shifts: POINTER(fmi3Float64),
    ) -> int:
        return self._call(
            "fmi3GetShiftDecimal",
            instance,
            valueReferences,
            nValueReferences,
            shifts,
        )

    def fmi3GetShiftFraction(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        counters: POINTER(fmi3UInt64),
        resolutions: POINTER(fmi3UInt64),
    ) -> int:
        return self._call(
            "fmi3GetShiftFraction",
            instance,
            valueReferences,
            nValueReferences,
            counters,
            resolutions,
        )

    def fmi3SetIntervalDecimal(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        intervals: POINTER(fmi3Float64),
    ) -> int:
        return self._call(
            "fmi3SetIntervalDecimal",
            instance,
            valueReferences,
            nValueReferences,
            intervals,
        )

    def fmi3SetIntervalFraction(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        counters: POINTER(fmi3UInt64),
        resolutions: POINTER(fmi3UInt64),
    ) -> int:
        return self._call(
            "fmi3SetIntervalFraction",
            instance,
            valueReferences,
            nValueReferences,
            counters,
            resolutions,
        )

    def fmi3SetShiftDecimal(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        shifts: POINTER(fmi3Float64),
    ) -> int:
        return self._call(
            "fmi3SetShiftDecimal",
            instance,
            valueReferences,
            nValueReferences,
            shifts,
        )

    def fmi3SetShiftFraction(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        counters: POINTER(fmi3UInt64),
        resolutions: POINTER(fmi3UInt64),
    ) -> int:
        return self._call(
            "fmi3SetShiftFraction",
            instance,
            valueReferences,
            nValueReferences,
            counters,
            resolutions,
        )

    def fmi3EvaluateDiscreteStates(
        self,
        instance: fmi3Instance,
    ) -> int:
        return self._call(
            "fmi3EvaluateDiscreteStates",
            instance,
        )

    def fmi3UpdateDiscreteStates(
        self,
        instance: fmi3Instance,
        discreteStatesNeedUpdate: POINTER(fmi3Boolean),
        terminateSimulation: POINTER(fmi3Boolean),
        nominalsOfContinuousStatesChanged: POINTER(fmi3Boolean),
        valuesOfContinuousStatesChanged: POINTER(fmi3Boolean),
        nextEventTimeDefined: POINTER(fmi3Boolean),
        nextEventTime: POINTER(fmi3Float64),
    ) -> int:
        return self._call(
            "fmi3UpdateDiscreteStates",
            instance,
            discreteStatesNeedUpdate,
            terminateSimulation,
            nominalsOfContinuousStatesChanged,
            valuesOfContinuousStatesChanged,
            nextEventTimeDefined,
            nextEventTime,
        )

    # Functions for Model Exchange

    def fmi3EnterContinuousTimeMode(
        self,
        instance: fmi3Instance,
    ) -> int:
        return self._call(
            "fmi3EnterContinuousTimeMode",
            instance,
        )

    def fmi3CompletedIntegratorStep(
        self,
        instance: fmi3Instance,
        noSetFMUStatePriorToCurrentPoint: fmi3Boolean | bool,
        enterEventMode: POINTER(fmi3Boolean),
        terminateSimulation: POINTER(fmi3Boolean),
    ) -> int:
        return self._call(
            "fmi3CompletedIntegratorStep",
            instance,
            noSetFMUStatePriorToCurrentPoint,
            enterEventMode,
            terminateSimulation,
        )

    #  Providing independent variables and re-initialization of caching

    def fmi3SetTime(
        self,
        instance: fmi3Instance,
        time: fmi3Float64 | float,
    ) -> int:
        return self._call(
            "fmi3SetTime",
            instance,
            time,
        )

    def fmi3SetContinuousStates(
        self,
        instance: fmi3Instance,
        continuousStates: POINTER(fmi3Float64),
        nContinuousStates: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3SetContinuousStates",
            instance,
            continuousStates,
            nContinuousStates,
        )

    # Evaluation of the model equations

    def fmi3GetContinuousStateDerivatives(
        self,
        instance: fmi3Instance,
        derivatives: POINTER(fmi3Float64),
        nContinuousStates: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetContinuousStateDerivatives",
            instance,
            derivatives,
            nContinuousStates,
        )

    def fmi3GetEventIndicators(
        self,
        instance: fmi3Instance,
        eventIndicators: POINTER(fmi3Float64),
        nEventIndicators: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetEventIndicators",
            instance,
            eventIndicators,
            nEventIndicators,
        )

    def fmi3GetContinuousStates(
        self,
        instance: fmi3Instance,
        continuousStates: POINTER(fmi3Float64),
        nContinuousStates: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetContinuousStates",
            instance,
            continuousStates,
            nContinuousStates,
        )

    def fmi3GetNominalsOfContinuousStates(
        self,
        instance: fmi3Instance,
        nominals: POINTER(fmi3Float64),
        nContinuousStates: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetNominalsOfContinuousStates",
            instance,
            nominals,
            nContinuousStates,
        )

    def fmi3GetNumberOfEventIndicators(
        self,
        instance: fmi3Instance,
        nEventIndicators: POINTER(c_size_t),
    ) -> int:
        return self._call(
            "fmi3GetNumberOfEventIndicators",
            instance,
            nEventIndicators,
        )

    def fmi3GetNumberOfContinuousStates(
        self,
        instance: fmi3Instance,
        nContinuousStates: POINTER(c_size_t),
    ) -> int:
        return self._call(
            "fmi3GetNumberOfContinuousStates",
            instance,
            nContinuousStates,
        )

    # Functions for Co-Simulation

    # Simulating the FMU

    def fmi3EnterStepMode(
        self,
        instance: fmi3Instance,
    ) -> int:
        return self._call(
            "fmi3EnterStepMode",
            instance,
        )

    def fmi3GetOutputDerivatives(
        self,
        instance: fmi3Instance,
        valueReferences: POINTER(fmi3ValueReference),
        nValueReferences: c_size_t | int,
        orders: POINTER(fmi3Int32),
        values: POINTER(fmi3Float64),
        nValues: c_size_t | int,
    ) -> int:
        return self._call(
            "fmi3GetOutputDerivatives",
            instance,
            valueReferences,
            nValueReferences,
            orders,
            values,
            nValues,
        )

    def fmi3DoStep(
        self,
        instance: fmi3Instance,
        currentCommunicationPoint: fmi3Float64 | float,
        communicationStepSize: fmi3Float64 | float,
        noSetFMUStatePriorToCurrentPoint: fmi3Boolean | bool,
        eventHandlingNeeded: POINTER(fmi3Boolean),
        terminateSimulation: POINTER(fmi3Boolean),
        earlyReturn: POINTER(fmi3Boolean),
        lastSuccessfulTime: POINTER(fmi3Float64),
    ) -> int:
        return self._call(
            "fmi3DoStep",
            instance,
            currentCommunicationPoint,
            communicationStepSize,
            noSetFMUStatePriorToCurrentPoint,
            eventHandlingNeeded,
            terminateSimulation,
            earlyReturn,
            lastSuccessfulTime,
        )

    # Functions for Scheduled Execution

    def fmi3ActivateModelPartition(
        self,
        instance: fmi3Instance,
        clockReference: fmi3ValueReference,
        activationTime: fmi3Float64 | float,
    ) -> int:
        return self._call(
            "fmi3ActivateModelPartition",
            instance,
            clockReference,
            activationTime,
        )

    # Inquire version numbers of header files and setting logging status

    def getVersion(self):
        version = self.fmi3GetVersion()
        return version.decode("utf-8")

    def setDebugLogging(self, loggingOn, categories):
        categories_ = (fmi3String * len(categories))()
        categories_[:] = [c.encode("utf-8") for c in categories]
        self.fmi3SetDebugLogging(
            self.component, fmi3Boolean(loggingOn), len(categories), categories_
        )

    # Creation and destruction of FMU instances and setting debug status

    def freeInstance(self):
        self.fmi3FreeInstance(self.component)
        self.freeLibrary()

    # Enter and exit initialization mode, terminate and reset

    def enterInitializationMode(self, tolerance=None, startTime=0.0, stopTime=None):
        toleranceDefined = fmi3Boolean(tolerance is not None)

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = fmi3Boolean(stopTime is not None)

        if stopTime is None:
            stopTime = 0.0

        self.fmi3EnterInitializationMode(
            self.component,
            toleranceDefined,
            tolerance,
            startTime,
            stopTimeDefined,
            stopTime,
        )

    def exitInitializationMode(self):
        self.fmi3ExitInitializationMode(self.component)

    # Clock related functions

    def getIntervalDecimal(self, valueReferences, intervals, qualifiers):
        self.fmi3GetIntervalDecimal(
            self.component,
            valueReferences,
            len(valueReferences),
            intervals,
            qualifiers,
            len(intervals),
        )

    def getIntervalFraction(
        self, valueReferences, intervalCounters, resolutions, qualifiers
    ):
        self.fmi3GetIntervalFraction(
            self.component,
            valueReferences,
            len(valueReferences),
            intervalCounters,
            resolutions,
            qualifiers,
            len(intervalCounters),
        )

    def getShiftDecimal(self, valueReferences, shifts):
        self.fmi3GetShiftDecimal(
            self.component, valueReferences, len(valueReferences), shifts, len(shifts)
        )

    def getShiftFraction(self, valueReferences, shiftCounters, resolutions):
        self.fmi3GetShiftFraction(
            self.component,
            valueReferences,
            len(valueReferences),
            shiftCounters,
            resolutions,
            len(shiftCounters),
        )

    def setIntervalDecimal(self, valueReferences, intervals):
        self.fmi3SetIntervalDecimal(
            self.component,
            valueReferences,
            len(valueReferences),
            intervals,
            len(intervals),
        )

    def setIntervalFraction(self, valueReferences, intervalCounters, resolutions):
        self.fmi3SetIntervalFraction(
            self.component,
            valueReferences,
            len(valueReferences),
            intervalCounters,
            resolutions,
            len(intervalCounters),
        )

    def enterEventMode(self):
        self.fmi3EnterEventMode(self.component)

    def updateDiscreteStates(self):
        discreteStatesNeedUpdate = fmi3Boolean()
        terminateSimulation = fmi3Boolean()
        nominalsOfContinuousStatesChanged = fmi3Boolean()
        valuesOfContinuousStatesChanged = fmi3Boolean()
        nextEventTimeDefined = fmi3Boolean()
        nextEventTime = fmi3Float64()

        self.fmi3UpdateDiscreteStates(
            self.component,
            byref(discreteStatesNeedUpdate),
            byref(terminateSimulation),
            byref(nominalsOfContinuousStatesChanged),
            byref(valuesOfContinuousStatesChanged),
            byref(nextEventTimeDefined),
            byref(nextEventTime),
        )

        return (
            discreteStatesNeedUpdate.value,
            terminateSimulation.value,
            nominalsOfContinuousStatesChanged.value,
            valuesOfContinuousStatesChanged.value,
            nextEventTimeDefined.value,
            nextEventTime.value,
        )

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

    def getString(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3String * nValues)()
        self.fmi3GetString(self.component, vr, len(vr), value, nValues)
        return list(map(lambda b: b.decode("utf-8"), value))

    def getBinary(self, vr: Iterable[int], nValues: int = None) -> Iterable[bytes]:
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Binary * nValues)()
        size = (c_size_t * nValues)()
        self.fmi3GetBinary(self.component, vr, len(vr), size, value, nValues)
        values = []
        for i, pointer in enumerate(value):
            if pointer:
                data = cast(pointer, POINTER(c_uint8 * size[i]))
                values.append(bytes(data.contents))
            else:
                values.append(None)
        return values

    def getClock(self, vr, nValues=None):
        if nValues is None:
            nValues = len(vr)
        vr = (fmi3ValueReference * len(vr))(*vr)
        value = (fmi3Clock * nValues)()
        self.fmi3GetClock(self.component, vr, len(vr), value, nValues)
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
        values = list(map(lambda s: s.encode("utf-8") if s is not None else s, values))
        values = (fmi3String * len(values))(*values)
        self.fmi3SetString(self.component, vr, len(vr), values, len(values))

    def setBinary(self, vr: Iterable[int], values: Iterable[bytes]):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values_ = (fmi3Binary * len(values))()
        for i, v in enumerate(values):
            b = (c_uint8 * len(v)).from_buffer(bytearray(v))
            values_[i] = b
        size = (c_size_t * len(values))(*[len(v) for v in values])
        self.fmi3SetBinary(self.component, vr, len(vr), size, values_, len(values))

    def setClock(self, vr, values):
        vr = (fmi3ValueReference * len(vr))(*vr)
        values = (fmi3Clock * len(values))(*values)
        self.fmi3SetClock(self.component, vr, len(vr), values, len(values))

    # Getting and setting the internal FMU state

    def getFMUState(self) -> fmi3FMUState:
        state = fmi3FMUState()
        self.fmi3GetFMUState(self.component, byref(state))
        return state

    def setFMUState(self, state: fmi3FMUState):
        self.fmi3SetFMUState(self.component, state)

    def freeFMUState(self, state: fmi3FMUState):
        self.fmi3FreeFMUState(self.component, byref(state))

    def serializeFMUState(self, state: fmi3FMUState) -> bytes:
        """Serialize an FMU state

        Parameters:
            state   the FMU state

        Returns:
            the serialized state as a byte string
        """

        size = c_size_t()
        self.fmi3SerializedFMUStateSize(self.component, state, byref(size))
        serializedState = create_string_buffer(size.value)
        self.fmi3SerializeFMUState(
            self.component, state, cast(serializedState, POINTER(fmi3Byte)), size
        )
        return serializedState.raw

    def deserializeFMUState(self, serializedState: bytes, state: fmi3FMUState = None):
        """De-serialize an FMU state

        Parameters:
            serializedState   the serialized state as a byte string
            state             the FMU state
        """
        if state is None:
            state = fmi3FMUState()
        buffer = create_string_buffer(serializedState, size=len(serializedState))
        self.fmi3DeserializeFMUState(
            self.component, cast(buffer, POINTER(fmi3Byte)), len(buffer), byref(state)
        )
        return state

    # Getting partial derivatives

    def getDirectionalDerivative(
        self,
        unknowns: Sequence[int],
        knowns: Sequence[int],
        seed: Sequence[float],
        nSensitivity: int = None,
    ) -> List[float]:
        """Get the directional derivatives

        Parameters:
            unknowns      list of value references of the unknowns
            knowns        list of value references of the knowns
            seed          list of delta values (one per known)
            nSensitivity  length of sensitivity

        Returns:
            sensitivity  list of the partial derivatives (one per unknown)
        """

        unknowns = (fmi3ValueReference * len(unknowns))(*unknowns)
        knowns = (fmi3ValueReference * len(knowns))(*knowns)
        seed = (fmi3Float64 * len(seed))(*seed)

        if nSensitivity is None:
            nSensitivity = len(unknowns)

        sensitivity = (fmi3Float64 * nSensitivity)()

        self.fmi3GetDirectionalDerivative(
            self.component,
            unknowns,
            len(unknowns),
            knowns,
            len(knowns),
            seed,
            len(seed),
            sensitivity,
            len(sensitivity),
        )

        return list(sensitivity)

    def getAdjointDerivative(
        self,
        unknowns: Sequence[int],
        knowns: Sequence[int],
        seed: Sequence[float],
        nSensitivity: int = None,
    ) -> List[float]:
        """Get adjoint derivatives

        Parameters:
            unknowns      list of value references of the unknowns
            knowns        list of value references of the knowns
            seed          list of delta values (one per known)
            nSensitivity  length of sensitivity

        Returns:
            sensitivity   list of the partial derivatives
        """

        unknowns = (fmi3ValueReference * len(unknowns))(*unknowns)
        knowns = (fmi3ValueReference * len(knowns))(*knowns)
        seed = (fmi3Float64 * len(seed))(*seed)

        if nSensitivity is None:
            nSensitivity = len(unknowns)

        sensitivity = (fmi3Float64 * nSensitivity)()

        self.fmi3GetAdjointDerivative(
            self.component,
            unknowns,
            len(unknowns),
            knowns,
            len(knowns),
            seed,
            len(seed),
            sensitivity,
            len(sensitivity),
        )

        return list(sensitivity)


class FMU3Model(_FMU3):
    """An FMI 3.0 Model Exchange FMU"""

    def __init__(self, **kwargs):
        super(FMU3Model, self).__init__(**kwargs)

    def instantiate(self, visible=False, loggingOn=False, logMessage=None):
        resourcePath = os.path.join(self.unzipDirectory, "resources") + os.path.sep

        # save callbacks from GC
        self.logMessage = fmi3LogMessageCallback(
            printLogMessage if logMessage is None else logMessage
        )

        self.component = self.fmi3InstantiateModelExchange(
            self.instanceName.encode("utf-8"),
            self.guid.encode("utf-8"),
            resourcePath.encode("utf-8"),
            fmi3Boolean(visible),
            fmi3Boolean(loggingOn),
            fmi3InstanceEnvironment(),
            self.logMessage,
        )

        if not self.component:
            raise Exception("Failed to instantiate FMU")

    # Enter and exit the different modes

    def enterContinuousTimeMode(self):
        return self.fmi3EnterContinuousTimeMode(self.component)

    def completedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint=True):
        enterEventMode = fmi3Boolean()
        terminateSimulation = fmi3Boolean()
        self.fmi3CompletedIntegratorStep(
            self.component,
            fmi3Boolean(noSetFMUStatePriorToCurrentPoint),
            byref(enterEventMode),
            byref(terminateSimulation),
        )
        return enterEventMode.value, terminateSimulation.value

    # Providing independent variables and re-initialization of caching

    def setTime(self, time):
        return self.fmi3SetTime(self.component, time)

    def setContinuousStates(self, continuousStates, nContinuousStates):
        return self.fmi3SetContinuousStates(
            self.component, continuousStates, nContinuousStates
        )

    # Evaluation of the model equations

    def getContinuousStateDerivatives(self, derivatives, nContinuousStates):
        return self.fmi3GetContinuousStateDerivatives(
            self.component, derivatives, nContinuousStates
        )

    def getEventIndicators(self, eventIndicators, nEventIndicators):
        return self.fmi3GetEventIndicators(
            self.component, eventIndicators, nEventIndicators
        )

    def getContinuousStates(self, continuousStates, nContinuousStates):
        return self.fmi3GetContinuousStates(
            self.component, continuousStates, nContinuousStates
        )

    def getNominalsOfContinuousStates(self, nominals, nContinuousStates):
        return self.fmi3GetNominalsOfContinuousStates(
            self.component, nominals, nContinuousStates
        )


class FMU3Slave(_FMU3):
    """An FMI 3.0 Co-Simulation FMU"""

    def __init__(self, instanceName=None, **kwargs):
        kwargs["instanceName"] = instanceName

        super(FMU3Slave, self).__init__(**kwargs)

    def instantiate(
        self,
        visible=False,
        loggingOn=False,
        eventModeUsed=False,
        earlyReturnAllowed=False,
        logMessage=None,
        intermediateUpdate=None,
    ):
        # save callbacks from GC
        self.logMessage = fmi3LogMessageCallback(
            printLogMessage if logMessage is None else logMessage
        )

        if intermediateUpdate is None:
            self.intermediateUpdate = fmi3IntermediateUpdateCallback()
        else:
            self.intermediateUpdate = fmi3IntermediateUpdateCallback(intermediateUpdate)

        resourcePath = os.path.join(self.unzipDirectory, "resources") + os.path.sep

        self.component = self.fmi3InstantiateCoSimulation(
            self.instanceName.encode("utf-8"),
            self.guid.encode("utf-8"),
            resourcePath.encode("utf-8"),
            fmi3Boolean(visible),
            fmi3Boolean(loggingOn),
            fmi3Boolean(eventModeUsed),
            fmi3Boolean(earlyReturnAllowed),
            None,
            0,
            fmi3InstanceEnvironment(),
            self.logMessage,
            self.intermediateUpdate,
        )

        if not self.component:
            raise Exception("Failed to instantiate FMU")

    # Simulating the FMU

    def enterStepMode(self):
        return self.fmi3EnterStepMode(self.component)

    def setInputDerivatives(self, vr, order, value):
        vr = (fmi3ValueReference * len(vr))(*vr)
        order = (fmi3Int32 * len(vr))(*order)
        value = (fmi3Float64 * len(vr))(*value)
        self.fmi3SetInputDerivatives(self.component, vr, len(vr), order, value)

    def getOutputDerivatives(self, vr, order):
        valueReferences = (fmi3ValueReference * len(vr))(*vr)
        orders = (fmi3Int32 * len(vr))(*order)
        values = (fmi3Float64 * len(vr))()
        self.fmi3GetOutputDerivatives(
            self.component,
            valueReferences,
            len(valueReferences),
            orders,
            values,
            len(values),
        )
        return list(values)

    def doStep(
        self,
        currentCommunicationPoint,
        communicationStepSize,
        noSetFMUStatePriorToCurrentPoint=True,
    ) -> Tuple[bool, bool, bool, float]:
        eventEncountered = fmi3Boolean()
        terminateSimulation = fmi3Boolean()
        earlyReturn = fmi3Boolean()
        lastSuccessfulTime = fmi3Float64()

        self.fmi3DoStep(
            self.component,
            currentCommunicationPoint,
            communicationStepSize,
            fmi3Boolean(noSetFMUStatePriorToCurrentPoint),
            byref(eventEncountered),
            byref(terminateSimulation),
            byref(earlyReturn),
            byref(lastSuccessfulTime),
        )

        return (
            eventEncountered.value,
            terminateSimulation.value,
            earlyReturn.value,
            lastSuccessfulTime.value,
        )


class FMU3ScheduledExecution(_FMU3):
    """An FMI 3.0 Scheduled Execution FMU"""

    def __init__(self, instanceName=None, **kwargs):
        kwargs["instanceName"] = instanceName
        super(FMU3ScheduledExecution, self).__init__(**kwargs)

    def instantiate(self, visible=False, loggingOn=False, logMessage=None):
        resourcePath = os.path.join(self.unzipDirectory, "resources") + os.path.sep

        def noop(*args):
            pass

        # save callbacks from GC
        self.logMessage = fmi3LogMessageCallback(
            printLogMessage if logMessage is None else logMessage
        )
        self.clockUpdate = fmi3ClockUpdateCallback(noop)
        self.lockPreemption = fmi3LockPreemptionCallback(noop)
        self.unlockPreemption = fmi3UnlockPreemptionCallback(noop)

        self.component = self.fmi3InstantiateScheduledExecution(
            self.instanceName.encode("utf-8"),
            self.guid.encode("utf-8"),
            resourcePath.encode("utf-8"),
            fmi3Boolean(visible),
            fmi3Boolean(loggingOn),
            fmi3InstanceEnvironment(),
            self.logMessage,
            self.clockUpdate,
            self.lockPreemption,
            self.unlockPreemption,
        )

        if not self.component:
            raise Exception("Failed to instantiate FMU")

    def activateModelPartition(self, clockReference, activationTime):
        self.fmi3ActivateModelPartition(self.component, clockReference, activationTime)
