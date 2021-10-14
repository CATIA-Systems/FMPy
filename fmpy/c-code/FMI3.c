/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#ifdef _WIN32
#include <direct.h>
#include "Shlwapi.h"
#pragma comment(lib, "shlwapi.lib")
#define strdup _strdup
#else
#include <stdarg.h>
#include <dlfcn.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "FMI3.h"


static void cb_logMessage3(fmi3InstanceEnvironment instanceEnvironment,
    fmi3String instanceName,
    fmi3Status status,
    fmi3String category,
    fmi3String message) {

    if (!instanceEnvironment) return;

    FMIInstance *instance = instanceEnvironment;

    if (!instance->logMessage) return;

    instance->logMessage(instance, status, category, message);
}

#if defined(FMI2_FUNCTION_PREFIX)
#define LOAD_SYMBOL(f) \
    instance->fmi3Functions->fmi3 ## f = fmi3 ## f;
#elif defined(_WIN32)
#define LOAD_SYMBOL(f) \
    instance->fmi3Functions->fmi3 ## f = (fmi3 ## f ## TYPE*)GetProcAddress(instance->libraryHandle, "fmi3" #f); \
    if (!instance->fmi3Functions->fmi3 ## f) { \
        instance->logMessage(instance, FMIError, "error", "Symbol fmi3" #f " is missing in shared library."); \
        return fmi3Error; \
    }
#else
#define LOAD_SYMBOL(f) \
    instance->fmi3Functions->fmi3 ## f = (fmi3 ## f ## TYPE*)dlsym(instance->libraryHandle, "fmi3" #f); \
    if (!instance->fmi3Functions->fmi3 ## f) { \
        instance->logMessage(instance, FMIError, "error", "Symbol fmi3" #f " is missing in shared library."); \
        return fmi3Error; \
    }
#endif

#define CALL(f) \
    fmi3Status status = instance->fmi3Functions->fmi3 ## f (instance->component); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi3" #f "()"); \
    } \
    instance->status = status > instance->status ? status : instance->status; \
    return status;

#define CALL_ARGS(f, m, ...) \
    fmi3Status status = instance->fmi3Functions-> fmi3 ## f (instance->component, __VA_ARGS__); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi3" #f "(" m ")", __VA_ARGS__); \
    } \
    instance->status = status > instance->status ? status : instance->status; \
    return status;

#define CALL_ARRAY(s, t) \
    fmi3Status status = instance->fmi3Functions->fmi3 ## s ## t(instance->component, valueReferences, nValueReferences, values, nValues); \
    if (instance->logFunctionCall) { \
        FMIValueReferencesToString(instance, valueReferences, nValueReferences); \
        FMIValuesToString(instance, nValues, values, FMI ## t ## Type); \
        instance->logFunctionCall(instance, status, "fmi3" #s #t "(valueReferences=%s, nValueReferences=%zu, values=%s, nValues=%zu)", instance->buf1, nValueReferences, instance->buf2, nValues); \
    } \
    instance->status = status > instance->status ? status : instance->status; \
    return status;

/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers and setting logging status */
const char* FMI3GetVersion(FMIInstance *instance) {
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi3GetVersion()");
    }
    return instance->fmi3Functions->fmi3GetVersion();
}

fmi3Status FMI3SetDebugLogging(FMIInstance *instance,
    fmi3Boolean loggingOn,
    size_t nCategories,
    const fmi3String categories[]) {
    fmi3Status status = instance->fmi3Functions->fmi3SetDebugLogging(instance->component, loggingOn, nCategories, categories);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nCategories, categories, FMIStringType);
        instance->logFunctionCall(instance, status, "fmi3SetDebugLogging(loggingOn=%d, nCategories=%zu, categories=%s)",
            loggingOn, nCategories, instance->buf2);
    }
    return status;
}

static fmi3Status loadSymbols3(FMIInstance *instance) {

#if !defined(FMI_VERSION) || FMI_VERSION == 3

    instance->fmi3Functions = calloc(1, sizeof(FMI3Functions));

    if (!instance->fmi3Functions) {
        return fmi3Error;
    }

    instance->fmiVersion = FMIVersion3;

    /***************************************************
    Common Functions
    ****************************************************/

    /* Inquire version numbers and set debug logging */
    LOAD_SYMBOL(GetVersion)
    LOAD_SYMBOL(SetDebugLogging)

    /* Creation and destruction of FMU instances */
    LOAD_SYMBOL(InstantiateModelExchange)
    LOAD_SYMBOL(InstantiateCoSimulation)
    LOAD_SYMBOL(InstantiateScheduledExecution)
    LOAD_SYMBOL(FreeInstance)

    /* Enter and exit initialization mode, terminate and reset */
    LOAD_SYMBOL(EnterInitializationMode)
    LOAD_SYMBOL(ExitInitializationMode)
    LOAD_SYMBOL(EnterEventMode)
    LOAD_SYMBOL(Terminate)
    LOAD_SYMBOL(Reset)

    /* Getting and setting variable values */
    LOAD_SYMBOL(GetFloat32)
    LOAD_SYMBOL(GetFloat64)
    LOAD_SYMBOL(GetInt8)
    LOAD_SYMBOL(GetUInt8)
    LOAD_SYMBOL(GetInt16)
    LOAD_SYMBOL(GetUInt16)
    LOAD_SYMBOL(GetInt32)
    LOAD_SYMBOL(GetUInt32)
    LOAD_SYMBOL(GetInt64)
    LOAD_SYMBOL(GetUInt64)
    LOAD_SYMBOL(GetBoolean)
    LOAD_SYMBOL(GetString)
    LOAD_SYMBOL(GetBinary)
    LOAD_SYMBOL(GetClock)
    LOAD_SYMBOL(SetFloat32)
    LOAD_SYMBOL(SetFloat64)
    LOAD_SYMBOL(SetInt8)
    LOAD_SYMBOL(SetUInt8)
    LOAD_SYMBOL(SetInt16)
    LOAD_SYMBOL(SetUInt16)
    LOAD_SYMBOL(SetInt32)
    LOAD_SYMBOL(SetUInt32)
    LOAD_SYMBOL(SetInt64)
    LOAD_SYMBOL(SetUInt64)
    LOAD_SYMBOL(SetBoolean)
    LOAD_SYMBOL(SetString)
    LOAD_SYMBOL(SetBinary)
    LOAD_SYMBOL(SetClock)

    /* Getting Variable Dependency Information */
    LOAD_SYMBOL(GetNumberOfVariableDependencies)
    LOAD_SYMBOL(GetVariableDependencies)

    /* Getting and setting the internal FMU state */
    LOAD_SYMBOL(GetFMUState)
    LOAD_SYMBOL(SetFMUState)
    LOAD_SYMBOL(FreeFMUState)
    LOAD_SYMBOL(SerializedFMUStateSize)
    LOAD_SYMBOL(SerializeFMUState)
    LOAD_SYMBOL(DeSerializeFMUState)

    /* Getting partial derivatives */
    LOAD_SYMBOL(GetDirectionalDerivative)
    LOAD_SYMBOL(GetAdjointDerivative)

    /* Entering and exiting the Configuration or Reconfiguration Mode */
    LOAD_SYMBOL(EnterConfigurationMode)
    LOAD_SYMBOL(ExitConfigurationMode)

    /* Clock related functions */
    LOAD_SYMBOL(GetIntervalDecimal)
    LOAD_SYMBOL(GetIntervalFraction)
    LOAD_SYMBOL(SetIntervalDecimal)
    LOAD_SYMBOL(SetIntervalFraction)
    LOAD_SYMBOL(UpdateDiscreteStates)

    /***************************************************
    Functions for Model Exchange
    ****************************************************/

    LOAD_SYMBOL(EnterContinuousTimeMode)
    LOAD_SYMBOL(CompletedIntegratorStep)

    /* Providing independent variables and re-initialization of caching */
    LOAD_SYMBOL(SetTime)
    LOAD_SYMBOL(SetContinuousStates)

    /* Evaluation of the model equations */
    LOAD_SYMBOL(GetContinuousStateDerivatives)
    LOAD_SYMBOL(GetEventIndicators)
    LOAD_SYMBOL(GetContinuousStates)
    LOAD_SYMBOL(GetNominalsOfContinuousStates)
    LOAD_SYMBOL(GetNumberOfEventIndicators)
    LOAD_SYMBOL(GetNumberOfContinuousStates)

    /***************************************************
    Functions for Co-Simulation
    ****************************************************/

    /* Simulating the FMU */
    LOAD_SYMBOL(EnterStepMode)
    LOAD_SYMBOL(GetOutputDerivatives)
    LOAD_SYMBOL(DoStep)
    LOAD_SYMBOL(ActivateModelPartition)

    instance->state = FMI2StartAndEndState;

    return fmi3OK;

#else

    return fmi3Error;

#endif
}

/* Creation and destruction of FMU instances and setting debug status */
fmi3Status FMI3InstantiateModelExchange(
    FMIInstance               *instance,
    fmi3String                 instantiationToken,
    fmi3String                 resourcePath,
    fmi3Boolean                visible,
    fmi3Boolean                loggingOn) {

    fmi3Status status = loadSymbols3(instance);

    fmi3CallbackLogMessage logMessage = instance->logMessage ? cb_logMessage3 : NULL;

    instance->component = instance->fmi3Functions->fmi3InstantiateModelExchange(instance->name, instantiationToken, resourcePath, visible, loggingOn, instance, logMessage);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, instance->component ? FMIOK : FMIError,
            "fmi3InstantiateModelExchange("
            "instanceName=\"%s\", "
            "instantiationToken=\"%s\", "
            "resourcePath=\"%s\", "
            "visible=%d, "
            "loggingOn=%d, "
            "instanceEnvironment=0x%p, "
            "logMessage=0x%p)",
            instance->name,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            instance,
            logMessage
        );
    }

    if (!instance->component) {
        return fmi3Error;
    }

    instance->interfaceType = FMIModelExchange;
    instance->state = FMI2InstantiatedState;

    return status;
}

fmi3Status FMI3InstantiateCoSimulation(
    FMIInstance                   *instance,
    fmi3String                     instantiationToken,
    fmi3String                     resourcePath,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    eventModeUsed,
    fmi3Boolean                    earlyReturnAllowed,
    const fmi3ValueReference       requiredIntermediateVariables[],
    size_t                         nRequiredIntermediateVariables,
    fmi3CallbackIntermediateUpdate intermediateUpdate) {

    if (loadSymbols3(instance) != FMIOK) {
        return fmi3Error;
    }

    fmi3CallbackLogMessage logMessage = instance->logMessage ? cb_logMessage3 : NULL;

    instance->component = instance->fmi3Functions->fmi3InstantiateCoSimulation(
        instance->name,
        instantiationToken,
        resourcePath,
        visible,
        loggingOn,
        eventModeUsed,
        earlyReturnAllowed,
        requiredIntermediateVariables,
        nRequiredIntermediateVariables,
        instance,
        logMessage,
        intermediateUpdate);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, instance->component ? FMIOK : FMIError,
            "fmi3InstantiateCoSimulation("
            "instanceName=\"%s\", "
            "instantiationToken=\"%s\", "
            "resourcePath=\"%s\", "
            "visible=%d, "
            "loggingOn=%d, "
            "eventModeUsed=%d, "
            "earlyReturnAllowed=%d, "
            "requiredIntermediateVariables=0x%p, "
            "nRequiredIntermediateVariables=%zu, "
            "instanceEnvironment=0x%p, "
            "logMessage=0x%p, "
            "intermediateUpdate=0x%p)",
            instance->name,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            eventModeUsed,
            earlyReturnAllowed,
            requiredIntermediateVariables,
            nRequiredIntermediateVariables,
            instance,
            logMessage,
            intermediateUpdate
        );
    }

    if (!instance->component) {
        return fmi3Error;
    }

    instance->interfaceType = FMICoSimulation;
    instance->state = FMI2InstantiatedState;

    return fmi3OK;
}

fmi3Status FMI3InstantiateScheduledExecution(
    FMIInstance                   *instance,
    fmi3String                     instantiationToken,
    fmi3String                     resourcePath,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    const fmi3ValueReference       requiredIntermediateVariables[],
    size_t                         nRequiredIntermediateVariables,
    fmi3CallbackIntermediateUpdate intermediateUpdate,
    fmi3CallbackLockPreemption     lockPreemption,
    fmi3CallbackUnlockPreemption   unlockPreemption) {

    if (loadSymbols3(instance) != FMIOK) {
        return fmi3Error;
    }

    fmi3CallbackLogMessage logMessage = instance->logMessage ? cb_logMessage3 : NULL;

    instance->component = instance->fmi3Functions->fmi3InstantiateScheduledExecution(
        instance->name,
        instantiationToken,
        resourcePath,
        visible,
        loggingOn,
        requiredIntermediateVariables,
        nRequiredIntermediateVariables,
        instance,
        logMessage,
        intermediateUpdate,
        lockPreemption,
        unlockPreemption);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, instance->component ? FMIOK : FMIError,
            "fmi3InstantiateScheduledExecution("
            "instanceName=\"%s\", "
            "instantiationToken=\"%s\", "
            "resourcePath=\"%s\", "
            "visible=%d, "
            "loggingOn=%d, "
            "requiredIntermediateVariables=0x%p, "
            "nRequiredIntermediateVariables=%zu, "
            "instanceEnvironment=0x%p, "
            "logMessage=0x%p, "
            "intermediateUpdate=0x%p, "
            "lockPreemption=0x%p, "
            "unlockPreemption=0x%p)",
            instance->name,
            instantiationToken,
            resourcePath,
            visible,
            loggingOn,
            requiredIntermediateVariables,
            nRequiredIntermediateVariables,
            instance,
            logMessage,
            intermediateUpdate,
            lockPreemption,
            unlockPreemption
        );
    }

    if (!instance->component) {
        return fmi3Error;
    }

    instance->interfaceType = FMIScheduledExecution;
    instance->state = FMI2InstantiatedState;

    return fmi3OK;
}

fmi3Status FMI3FreeInstance(FMIInstance *instance) {

    instance->fmi3Functions->fmi3FreeInstance(instance->component);

    instance->component = NULL;

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, fmi3OK, "fmi3FreeInstance()");
    }

    return fmi3OK;
}

/* Enter and exit initialization mode, enter event mode, terminate and reset */
fmi3Status FMI3EnterInitializationMode(FMIInstance *instance,
    fmi3Boolean toleranceDefined,
    fmi3Float64 tolerance,
    fmi3Float64 startTime,
    fmi3Boolean stopTimeDefined,
    fmi3Float64 stopTime) {

    instance->state = FMI2InitializationModeState;

    CALL_ARGS(EnterInitializationMode,
        "fmi3EnterInitializationMode(toleranceDefined=%d, tolerance=%.16g, startTime=%.16g, stopTimeDefined=%d, stopTime=%.16g)",
        toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime)
}

fmi3Status FMI3ExitInitializationMode(FMIInstance *instance) {

    instance->state = instance->interfaceType == FMIModelExchange ? FMI2EventModeState : FMI2StepCompleteState;

    CALL(ExitInitializationMode)
}

fmi3Status FMI3EnterEventMode(FMIInstance *instance,
    fmi3Boolean stepEvent,
    fmi3Boolean stateEvent,
    const fmi3Int32 rootsFound[],
    size_t nEventIndicators,
    fmi3Boolean timeEvent) {

    fmi3Status status = instance->fmi3Functions->fmi3EnterEventMode(instance->component, stepEvent, stateEvent, rootsFound, nEventIndicators, timeEvent);

    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nEventIndicators, rootsFound, FMIInt32Type);
        instance->logFunctionCall(instance, status,
            "fmi3EnterEventMode(stepEvent=%d, stateEvent=%d, rootsFound=%s, nEventIndicators=%zu, timeEvent=%d)",
            stepEvent, stateEvent, instance->buf2, nEventIndicators, timeEvent);
    }

    return status;
}

fmi3Status FMI3Terminate(FMIInstance *instance) {
    instance->state = FMI2TerminatedState;
    CALL(Terminate)
}

fmi3Status FMI3Reset(FMIInstance *instance) {
    instance->state = FMI2InstantiatedState;
    CALL(Reset)
}

/* Getting and setting variable values */
fmi3Status FMI3GetFloat32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float32 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Float32)
}

fmi3Status FMI3GetFloat64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Float64)
}

fmi3Status FMI3GetInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int8 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Int8)
}

fmi3Status FMI3GetUInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt8 values[],
    size_t nValues) {
    CALL_ARRAY(Get, UInt8)
}

fmi3Status FMI3GetInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int16 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Int16)
}

fmi3Status FMI3GetUInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt16 values[],
    size_t nValues) {
    CALL_ARRAY(Get, UInt16)
}

fmi3Status FMI3GetInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int32 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Int32)
}

fmi3Status FMI3GetUInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt32 values[],
    size_t nValues) {
    CALL_ARRAY(Get, UInt32)
}

fmi3Status FMI3GetInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int64 values[],
    size_t nValues) {
    CALL_ARRAY(Get, Int64)
}

fmi3Status FMI3GetUInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt64 values[],
    size_t nValues) {
    CALL_ARRAY(Get, UInt64)
}

fmi3Status FMI3GetBoolean(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Boolean values[],
    size_t nValues) {
    CALL_ARRAY(Get, Boolean)
}

fmi3Status FMI3GetString(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3String values[],
    size_t nValues) {
    CALL_ARRAY(Get, String)
}

fmi3Status FMI3GetBinary(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    size_t sizes[],
    fmi3Binary values[],
    size_t nValues) {

    fmi3Status status = instance->fmi3Functions->fmi3GetBinary(instance->component, valueReferences, nValueReferences, sizes, values, nValues);

    if (instance->logFunctionCall) {
        FMIValueReferencesToString(instance, valueReferences, nValueReferences);
        FMIValuesToString(instance, nValues, values, FMIBinaryType);
        instance->logFunctionCall(instance, status, "fmi3GetBinary(valueReferences=%s, nValueReferences=%zu, sizes=%p, values=%s, nValues=%zu)", instance->buf1, nValueReferences, sizes, instance->buf2, nValues);
    }

    return status;
}

fmi3Status FMI3GetClock(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Clock values[],
    size_t nValues) {
    CALL_ARRAY(Get, Clock)
}

fmi3Status FMI3SetFloat32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float32 values[],
    size_t nValues)    {
    CALL_ARRAY(Set, Float32)
}

fmi3Status FMI3SetFloat64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float64 values[],
    size_t nValues) {
    CALL_ARRAY(Set, Float64)
}

fmi3Status FMI3SetInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int8 values[],
    size_t nValues) {
    CALL_ARRAY(Set, Int8)
}

fmi3Status FMI3SetUInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt8 values[],
    size_t nValues) {
    CALL_ARRAY(Set, UInt8)
}

fmi3Status FMI3SetInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int16 values[],
    size_t nValues) {
    CALL_ARRAY(Set, Int16)
}

fmi3Status FMI3SetUInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt16 values[],
    size_t nValues) {
    CALL_ARRAY(Set, UInt16)
}

fmi3Status FMI3SetInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 values[],
    size_t nValues) {
    CALL_ARRAY(Set, Int32)
}

fmi3Status FMI3SetUInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt32 values[],
    size_t nValues) {
    CALL_ARRAY(Set, UInt32)
}

fmi3Status FMI3SetInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int64 values[],
    size_t nValues) {
    CALL_ARRAY(Set, Int64)
}

fmi3Status FMI3SetUInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt64 values[],
    size_t nValues) {
    CALL_ARRAY(Set, UInt64)
}

fmi3Status FMI3SetBoolean(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Boolean values[],
    size_t nValues) {
    CALL_ARRAY(Set, Boolean)
}

fmi3Status FMI3SetString(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3String values[],
    size_t nValues) {
    CALL_ARRAY(Set, String)
}

fmi3Status FMI3SetBinary(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const size_t sizes[],
    const fmi3Binary values[],
    size_t nValues) {

    fmi3Status status = instance->fmi3Functions->fmi3SetBinary(instance->component, valueReferences, nValueReferences, sizes, values, nValues);

    if (instance->logFunctionCall) {
        FMIValueReferencesToString(instance, valueReferences, nValueReferences);
        FMIValuesToString(instance, nValues, values, FMIBinaryType);
        instance->logFunctionCall(instance, status, "fmi3SetBinary(valueReferences=%s, nValueReferences=%zu, sizes=0x%p, values=%s, nValues=%zu", instance->buf1, nValueReferences, sizes, instance->buf2, nValues);
    }

    return status;
}

fmi3Status FMI3SetClock(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Clock values[],
    size_t nValues) {
    CALL_ARRAY(Set, Clock)
}

/* Getting Variable Dependency Information */
fmi3Status FMI3GetNumberOfVariableDependencies(FMIInstance *instance,
    fmi3ValueReference valueReference,
    size_t* nDependencies) {
    CALL_ARGS(GetNumberOfVariableDependencies, "valueReference=%u, nDependencies=0x%p", valueReference, nDependencies)
}

fmi3Status FMI3GetVariableDependencies(FMIInstance *instance,
    fmi3ValueReference dependent,
    size_t elementIndicesOfDependent[],
    fmi3ValueReference independents[],
    size_t elementIndicesOfIndependents[],
    fmi3DependencyKind dependencyKinds[],
    size_t nDependencies) {
    CALL_ARGS(GetVariableDependencies, "dependent=%u, elementIndicesOfDependent=0x%p, independents=0x%p, elementIndicesOfIndependents=0x%p, dependencyKinds=0x%p, nDependencies=%zu",
        dependent, elementIndicesOfDependent, independents, elementIndicesOfIndependents, dependencyKinds, nDependencies)
}

/* Getting and setting the internal FMU state */
fmi3Status FMI3GetFMUState(FMIInstance *instance, fmi3FMUState* FMUState) {
    CALL_ARGS(GetFMUState, "FMUState=0x%p", FMUState)
}

fmi3Status FMI3SetFMUState(FMIInstance *instance, fmi3FMUState  FMUState) {
    CALL_ARGS(SetFMUState, "FMUState=0x%p", FMUState)
}

fmi3Status FMI3FreeFMUState(FMIInstance *instance, fmi3FMUState* FMUState) {
    CALL_ARGS(FreeFMUState, "FMUState=0x%p", FMUState)
}


fmi3Status FMI3SerializedFMUStateSize(FMIInstance *instance,
    fmi3FMUState  FMUState,
    size_t* size) {
    fmi3Status status = instance->fmi3Functions->fmi3SerializedFMUStateSize(instance->component, FMUState, size);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi3SerializedFMUStateSize(FMUState=0x%p, size=%zu)", FMUState, *size);
    }
    return status;
}

fmi3Status FMI3SerializeFMUState(FMIInstance *instance,
    fmi3FMUState  FMUState,
    fmi3Byte serializedState[],
    size_t size) {
    CALL_ARGS(SerializeFMUState, "FMUstate=0x%p, serializedState=0x%p, size=%zu", FMUState, serializedState, size);
}

fmi3Status FMI3DeSerializeFMUState(FMIInstance *instance,
    const fmi3Byte serializedState[],
    size_t size,
    fmi3FMUState* FMUState) {
    CALL_ARGS(DeSerializeFMUState, "serializedState=0x%p, size=%zu, FMUState=0x%p", serializedState, size, FMUState);
}

/* Getting partial derivatives */
fmi3Status FMI3GetDirectionalDerivative(FMIInstance *instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity) {
    CALL_ARGS(GetDirectionalDerivative,
        "unknowns=0x%p, nUnknowns=%zu, knowns=0x%p, nKnowns=%zu, seed=0x%p, nSeed=%zu, sensitivity=0x%p, nSensitivity=%zu",
        unknowns, nUnknowns, knowns, nKnowns, seed, nSeed, sensitivity, nSensitivity);
}

fmi3Status FMI3GetAdjointDerivative(FMIInstance *instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity) {
    CALL_ARGS(GetAdjointDerivative,
        "unknowns=0x%p, nUnknowns=%zu, knowns=0x%p, nKnowns=%zu, seed=0x%p, nSeed=%zu, sensitivity=0x%p, nSensitivity=%zu",
        unknowns, nUnknowns, knowns, nKnowns, seed, nSeed, sensitivity, nSensitivity);
}

/* Entering and exiting the Configuration or Reconfiguration Mode */
fmi3Status FMI3EnterConfigurationMode(FMIInstance *instance) {
    CALL(EnterConfigurationMode)
}

fmi3Status FMI3ExitConfigurationMode(FMIInstance *instance) {
    CALL(ExitConfigurationMode)
}

/* Clock related functions */

FMI_STATIC fmi3Status FMI3GetIntervalDecimal(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 intervals[],
    fmi3IntervalQualifier qualifiers[],
    size_t nIntervals) {
    CALL_ARGS(GetIntervalDecimal,
        "valueReferences=0x%p, nValueReferences=%zu, intervals=0x%p, qualifiers=0x%p, nIntervals=%zu",
        valueReferences, nValueReferences, intervals, qualifiers, nIntervals);
}

//fmi3Status FMI3GetIntervalFraction(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    fmi3UInt64 intervalCounter[],
//    fmi3UInt64 resolution[],
//    size_t nValues) {
//    CALL_ARGS(GetIntervalFraction,
//        "valueReferences=0x%p, nValueReferences=%zu, intervalCounter=0x%p, resolution=0x%p, nValues=%zu",
//        valueReferences, nValueReferences, intervalCounter, resolution, nValues);
//}
//
//fmi3Status FMI3SetIntervalDecimal(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    const fmi3Float64 interval[],
//    size_t nValues) {
//    CALL_ARGS(SetIntervalDecimal,
//        "valueReferences=0x%p, nValueReferences=%zu, interval=0x%p, nValues=%zu",
//        valueReferences, nValueReferences, interval, nValues);
//}
//
//fmi3Status FMI3SetIntervalFraction(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    const fmi3UInt64 intervalCounter[],
//    const fmi3UInt64 resolution[],
//    size_t nValues) {
//    CALL_ARGS(SetIntervalFraction,
//        "valueReferences=0x%p, nValueReferences=%zu, intervalCounter=0x%p, resolution=0x%p, nValues=%zu",
//        valueReferences, nValueReferences, intervalCounter, resolution, nValues);
//}

fmi3Status FMI3UpdateDiscreteStates(FMIInstance *instance,
    fmi3Boolean *discreteStatesNeedUpdate,
    fmi3Boolean *terminateSimulation,
    fmi3Boolean *nominalsOfContinuousStatesChanged,
    fmi3Boolean *valuesOfContinuousStatesChanged,
    fmi3Boolean *nextEventTimeDefined,
    fmi3Float64 *nextEventTime) {

    fmi3Status status = instance->fmi3Functions->fmi3UpdateDiscreteStates(instance->component, discreteStatesNeedUpdate, terminateSimulation, nominalsOfContinuousStatesChanged, valuesOfContinuousStatesChanged, nextEventTimeDefined, nextEventTime);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi3UpdateDiscreteStates(discreteStatesNeedUpdate=%d, terminateSimulation=%d, nominalsOfContinuousStatesChanged=%d, valuesOfContinuousStatesChanged=%d, nextEventTimeDefined=%d, nextEventTime=%.16g)",
            *discreteStatesNeedUpdate, *terminateSimulation, *nominalsOfContinuousStatesChanged, *valuesOfContinuousStatesChanged, *nextEventTimeDefined, *nextEventTime);
    }

    return status;
}

/***************************************************
Types for Functions for Model Exchange
****************************************************/

fmi3Status FMI3EnterContinuousTimeMode(FMIInstance *instance) {
    instance->state = FMI2ContinuousTimeModeState;
    CALL(EnterContinuousTimeMode)
}

fmi3Status FMI3CompletedIntegratorStep(FMIInstance *instance,
    fmi3Boolean noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* enterEventMode,
    fmi3Boolean* terminateSimulation) {

    fmi3Status status = instance->fmi3Functions->fmi3CompletedIntegratorStep(instance->component, noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi3CompletedIntegratorStep(noSetFMUStatePriorToCurrentPoint=%d, enterEventMode=%d, terminateSimulation=%d)",
            noSetFMUStatePriorToCurrentPoint, *enterEventMode, *terminateSimulation);
    }

    return status;
}

/* Providing independent variables and re-initialization of caching */
fmi3Status FMI3SetTime(FMIInstance *instance, fmi3Float64 time) {
    instance->time = time;
    CALL_ARGS(SetTime, "time=%.16g", time);
}

fmi3Status FMI3SetContinuousStates(FMIInstance *instance,
    const fmi3Float64 continuousStates[],
    size_t nContinuousStates) {

    fmi3Status status = instance->fmi3Functions->fmi3SetContinuousStates(instance->component, continuousStates, nContinuousStates);

    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nContinuousStates, continuousStates, FMIFloat64Type);
        instance->logFunctionCall(instance, status,
            "fmi3SetContinuousStates(continuousStates=%s, nContinuousStates=%zu)",
            instance->buf2, nContinuousStates);
    }

    return status;
}

/* Evaluation of the model equations */
fmi3Status FMI3GetContinuousStateDerivatives(FMIInstance *instance,
    fmi3Float64 derivatives[],
    size_t nContinuousStates) {

    fmi3Status status = instance->fmi3Functions->fmi3GetContinuousStateDerivatives(instance->component, derivatives, nContinuousStates);

    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nContinuousStates, derivatives, FMIFloat64Type);
        instance->logFunctionCall(instance, status,
            "fmi3GetDerivatives(derivatives=%s, nContinuousStates=%zu)",
            instance->buf2, nContinuousStates);
    }

    return status;
}

fmi3Status FMI3GetEventIndicators(FMIInstance *instance,
    fmi3Float64 eventIndicators[],
    size_t nEventIndicators) {

    fmi3Status status = instance->fmi3Functions->fmi3GetEventIndicators(instance->component, eventIndicators, nEventIndicators);

    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nEventIndicators, eventIndicators, FMIFloat64Type);
        instance->logFunctionCall(instance, status,
            "fmi3GetEventIndicators(eventIndicators=%s, nEventIndicators=%zu)",
            instance->buf2, nEventIndicators);
    }

    return status;
}

fmi3Status FMI3GetContinuousStates(FMIInstance *instance,
    fmi3Float64 continuousStates[],
    size_t nContinuousStates) {

    fmi3Status status = instance->fmi3Functions->fmi3GetContinuousStates(instance->component, continuousStates, nContinuousStates);

    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nContinuousStates, continuousStates, FMIFloat64Type);
        instance->logFunctionCall(instance, status,
            "fmi3GetContinuousStates(continuousStates=%s, nContinuousStates=%zu)",
            instance->buf2, nContinuousStates);
    }

    return status;
}

fmi3Status FMI3GetNominalsOfContinuousStates(FMIInstance *instance,
    fmi3Float64 nominals[],
    size_t nContinuousStates) {
    CALL_ARGS(GetNominalsOfContinuousStates, "nominals=0x%p, nContinuousStates=%zu", nominals, nContinuousStates);
}


fmi3Status FMI3GetNumberOfEventIndicators(FMIInstance *instance,
    size_t* nEventIndicators) {
    CALL_ARGS(GetNumberOfEventIndicators, "nEventIndicators=0x%p", nEventIndicators);
}

fmi3Status FMI3GetNumberOfContinuousStates(FMIInstance *instance,
    size_t* nContinuousStates) {
    CALL_ARGS(GetNumberOfContinuousStates, "nContinuousStates=0x%p", nContinuousStates);
}

/***************************************************
Types for Functions for Co-Simulation
****************************************************/

/* Simulating the FMU */

fmi3Status FMI3EnterStepMode(FMIInstance *instance) {
    CALL(EnterStepMode)
}

fmi3Status FMI3GetOutputDerivatives(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 orders[],
    fmi3Float64 values[],
    size_t nValues) {
    CALL_ARGS(GetOutputDerivatives,
        "valueReferences=0x%p, nValueReferences=%zu, orders=0x%p, values=0x%p, nValues=%zu",
        valueReferences, nValueReferences, orders, values, nValues);
}

fmi3Status FMI3DoStep(FMIInstance *instance,
    fmi3Float64 currentCommunicationPoint,
    fmi3Float64 communicationStepSize,
    fmi3Boolean noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* eventEncountered,
    fmi3Boolean* terminate,
    fmi3Boolean* earlyReturn,
    fmi3Float64* lastSuccessfulTime) {

    fmi3Status status = instance->fmi3Functions->fmi3DoStep(instance->component, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint, eventEncountered, terminate, earlyReturn, lastSuccessfulTime);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi3DoStep(currentCommunicationPoint=%.16g, communicationStepSize=%.16g, noSetFMUStatePriorToCurrentPoint=%d, eventEncountered=%d, terminate=%d, earlyReturn=%d, lastSuccessfulTime=%.16g",
            currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint, *eventEncountered, *terminate, *earlyReturn, *lastSuccessfulTime);
    }

    instance->time = *lastSuccessfulTime;

    return status;
}

fmi3Status FMI3ActivateModelPartition(FMIInstance *instance,
    fmi3ValueReference clockReference,
    size_t clockElementIndex,
    fmi3Float64 activationTime) {
    CALL_ARGS(ActivateModelPartition,
        "clockReference=%u, clockElementIndex=%zu, activationTime=%.16g",
        clockReference, clockElementIndex, activationTime);
}

#undef LOAD_SYMBOL
#undef CALL
#undef CALL_ARGS
#undef CALL_ARRAY
