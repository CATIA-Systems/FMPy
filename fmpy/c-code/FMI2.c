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
#define INTERNET_MAX_URL_LENGTH 2083 // from wininet.h
#else
#include <stdarg.h>
#include <dlfcn.h>
#endif

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "FMI2.h"


static void cb_logMessage2(fmi2ComponentEnvironment componentEnvironment, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {

    if (!componentEnvironment) return;

    FMIInstance *instance = componentEnvironment;

    char buf[FMI_MAX_MESSAGE_LENGTH];

    va_list args;

    va_start(args, message);
    vsnprintf(buf, FMI_MAX_MESSAGE_LENGTH, message, args);
    va_end(args);

    if (!instance->logMessage) return;

    instance->logMessage(instance, status, category, buf);
}

#if defined(FMI2_FUNCTION_PREFIX)
#define LOAD_SYMBOL(f) \
    instance->fmi2Functions->fmi2 ## f = fmi2 ## f;
#elif defined(_WIN32)
#define LOAD_SYMBOL(f) \
    instance->fmi2Functions->fmi2 ## f = (fmi2 ## f ## TYPE*)GetProcAddress(instance->libraryHandle, "fmi2" #f); \
    if (!instance->fmi2Functions->fmi2 ## f) { \
        instance->logMessage(instance, FMIError, "error", "Symbol fmi2" #f " is missing in shared library."); \
        goto fail; \
    }
#else
#define LOAD_SYMBOL(f) \
    instance->fmi2Functions->fmi2 ## f = (fmi2 ## f ## TYPE*)dlsym(instance->libraryHandle, "fmi2" #f); \
    if (!instance->fmi2Functions->fmi2 ## f) { \
        instance->logMessage(instance, FMIError, "error", "Symbol fmi2" #f " is missing in shared library."); \
        goto fail; \
    }
#endif

#define CALL(f) \
    fmi2Status status = instance->fmi2Functions->fmi2 ## f (instance->component); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi2" #f "()"); \
    } \
    return status;

#define CALL_ARGS(f, m, ...) \
    fmi2Status status = instance->fmi2Functions-> fmi2 ## f (instance->component, __VA_ARGS__); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi2" #f "(" m ")", __VA_ARGS__); \
    } \
    return status;

#define CALL_ARRAY(s, t) \
    fmi2Status status = instance->fmi2Functions->fmi2 ## s ## t(instance->component, vr, nvr, value); \
    if (instance->logFunctionCall) { \
        FMIValueReferencesToString(instance, vr, nvr); \
        FMIValuesToString(instance, nvr, value, FMI ## t ## Type); \
        instance->logFunctionCall(instance, status, "fmi2" #s #t "(vr=%s, nvr=%zu, value=%s)", instance->buf1, nvr, instance->buf2); \
    } \
    return status;

/***************************************************
Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
const char* FMI2GetTypesPlatform(FMIInstance *instance) {
    if (instance->logFunctionCall) {
            instance->logFunctionCall(instance, FMIOK, "fmi2GetTypesPlatform()");
    }
    return instance->fmi2Functions->fmi2GetTypesPlatform();
}

const char* FMI2GetVersion(FMIInstance *instance) {
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi2GetVersion()");
    }
    return instance->fmi2Functions->fmi2GetVersion();
}

fmi2Status FMI2SetDebugLogging(FMIInstance *instance, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {
    fmi2Status status = instance->fmi2Functions->fmi2SetDebugLogging(instance->component, loggingOn, nCategories, categories);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nCategories, categories, FMIStringType);
        instance->logFunctionCall(instance, status, "fmi2SetDebugLogging(loggingOn=%d, nCategories=%zu, categories=%s)",
            loggingOn, nCategories, instance->buf2);
    }
    return status;
}

/* Creation and destruction of FMU instances and setting debug status */
fmi2Status FMI2Instantiate(FMIInstance *instance, const char *fmuResourceLocation, fmi2Type fmuType, fmi2String fmuGUID,
    fmi2Boolean visible, fmi2Boolean loggingOn) {

    instance->fmiVersion = FMIVersion2;

    instance->fmi2Functions = calloc(1, sizeof(FMI2Functions));

    if (!instance->fmi2Functions) {
        return fmi2Error;
    }

    instance->fmi2Functions->eventInfo.newDiscreteStatesNeeded           = fmi2False;
    instance->fmi2Functions->eventInfo.terminateSimulation               = fmi2False;
    instance->fmi2Functions->eventInfo.nominalsOfContinuousStatesChanged = fmi2False;
    instance->fmi2Functions->eventInfo.valuesOfContinuousStatesChanged   = fmi2False;
    instance->fmi2Functions->eventInfo.nextEventTimeDefined              = fmi2False;
    instance->fmi2Functions->eventInfo.nextEventTime                     = 0.0;

    instance->state = FMI2StartAndEndState;

#if !defined(FMI_VERSION) || FMI_VERSION == 2

    /***************************************************
    Common Functions
    ****************************************************/

    /* required functions */
    LOAD_SYMBOL(GetTypesPlatform)
    LOAD_SYMBOL(GetVersion)
    LOAD_SYMBOL(SetDebugLogging)
    LOAD_SYMBOL(Instantiate)
    LOAD_SYMBOL(FreeInstance)
    LOAD_SYMBOL(SetupExperiment)
    LOAD_SYMBOL(EnterInitializationMode)
    LOAD_SYMBOL(ExitInitializationMode)
    LOAD_SYMBOL(Terminate)
    LOAD_SYMBOL(Reset)
    LOAD_SYMBOL(GetReal)
    LOAD_SYMBOL(GetInteger)
    LOAD_SYMBOL(GetBoolean)
    LOAD_SYMBOL(GetString)
    LOAD_SYMBOL(SetReal)
    LOAD_SYMBOL(SetInteger)
    LOAD_SYMBOL(SetBoolean)
    LOAD_SYMBOL(SetString)

    /* optional functions */
    LOAD_SYMBOL(GetFMUstate)
    LOAD_SYMBOL(SetFMUstate)
    LOAD_SYMBOL(FreeFMUstate)
    LOAD_SYMBOL(SerializedFMUstateSize)
    LOAD_SYMBOL(SerializeFMUstate)
    LOAD_SYMBOL(DeSerializeFMUstate)
    LOAD_SYMBOL(GetDirectionalDerivative)

    if (fmuType == fmi2ModelExchange) {
#ifndef CO_SIMULATION
        /***************************************************
        Model Exchange
        ****************************************************/

        LOAD_SYMBOL(EnterEventMode)
        LOAD_SYMBOL(NewDiscreteStates)
        LOAD_SYMBOL(EnterContinuousTimeMode)
        LOAD_SYMBOL(CompletedIntegratorStep)
        LOAD_SYMBOL(SetTime)
        LOAD_SYMBOL(SetContinuousStates)
        LOAD_SYMBOL(GetDerivatives)
        LOAD_SYMBOL(GetEventIndicators)
        LOAD_SYMBOL(GetContinuousStates)
        LOAD_SYMBOL(GetNominalsOfContinuousStates)
#endif
    } else {
#ifndef MODEL_EXCHANGE
        /***************************************************
        Co-Simulation
        ****************************************************/

        LOAD_SYMBOL(SetRealInputDerivatives)
        LOAD_SYMBOL(GetRealOutputDerivatives)
        LOAD_SYMBOL(DoStep)
        LOAD_SYMBOL(CancelStep)
        LOAD_SYMBOL(GetStatus)
        LOAD_SYMBOL(GetRealStatus)
        LOAD_SYMBOL(GetIntegerStatus)
        LOAD_SYMBOL(GetBooleanStatus)
        LOAD_SYMBOL(GetStringStatus)
#endif
    }


#endif

    instance->fmi2Functions->callbacks.logger               = cb_logMessage2;
    instance->fmi2Functions->callbacks.allocateMemory       = calloc;
    instance->fmi2Functions->callbacks.freeMemory           = free;
    instance->fmi2Functions->callbacks.stepFinished         = NULL;
    instance->fmi2Functions->callbacks.componentEnvironment = instance;

    instance->component = instance->fmi2Functions->fmi2Instantiate(instance->name, fmuType, fmuGUID, fmuResourceLocation, &instance->fmi2Functions->callbacks, visible, loggingOn);

    if (instance->logFunctionCall) {
        fmi2CallbackFunctions *f = &instance->fmi2Functions->callbacks;
        instance->logFunctionCall(instance, instance->component ? FMIOK : FMIError,
            "fmi2Instantiate(instanceName=\"%s\", fmuType=%d, fmuGUID=\"%s\", fmuResourceLocation=\"%s\", functions={logger=0x%p, allocateMemory=0x%p, freeMemory=0x%p, stepFinished=0x%p, componentEnvironment=0x%p}, visible=%d, loggingOn=%d)",
            instance->name, fmuType, fmuGUID, fmuResourceLocation, f->logger, f->allocateMemory, f->freeMemory, f->stepFinished, f->componentEnvironment, visible, loggingOn);
    }

    if (!instance->component) goto fail;

    instance->state = FMI2InstantiatedState;

    return fmi2OK;

fail:
    return fmi2Error;
}

void FMI2FreeInstance(FMIInstance *instance) {

    instance->fmi2Functions->fmi2FreeInstance(instance->component);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi2FreeInstance()");
    }
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status FMI2SetupExperiment(FMIInstance *instance,
    fmi2Boolean toleranceDefined,
    fmi2Real tolerance,
    fmi2Real startTime,
    fmi2Boolean stopTimeDefined,
    fmi2Real stopTime) {

    instance->time = startTime;

    CALL_ARGS(SetupExperiment, "toleranceDefined=%d, tolerance=%.16g, startTime=%.16g, stopTimeDefined=%d, stopTime=%.16g", toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime);
}

fmi2Status FMI2EnterInitializationMode(FMIInstance *instance) {
    instance->state = FMI2InitializationModeState;
    CALL(EnterInitializationMode)
}

fmi2Status FMI2ExitInitializationMode(FMIInstance *instance) {
    instance->state = instance->interfaceType == FMIModelExchange ? FMI2EventModeState : FMI2StepCompleteState;
    CALL(ExitInitializationMode)
}

fmi2Status FMI2Terminate(FMIInstance *instance) {
    instance->state = FMI2TerminatedState;
    CALL(Terminate)
}

fmi2Status FMI2Reset(FMIInstance *instance) {
    instance->state = FMI2InstantiatedState;
    CALL(Reset)
}

/* Getting and setting variable values */
fmi2Status FMI2GetReal(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
    CALL_ARRAY(Get, Real)
}

fmi2Status FMI2GetInteger(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
    CALL_ARRAY(Get, Integer)
}

fmi2Status FMI2GetBoolean(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {
    CALL_ARRAY(Get, Boolean)
}

fmi2Status FMI2GetString(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2String value[]) {
    CALL_ARRAY(Get, String)
}

fmi2Status FMI2SetReal(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {
    CALL_ARRAY(Set, Real)
}

fmi2Status FMI2SetInteger(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
    CALL_ARRAY(Set, Integer)
}

fmi2Status FMI2SetBoolean(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {
    CALL_ARRAY(Set, Boolean)
}

fmi2Status FMI2SetString(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2String value[]) {
    CALL_ARRAY(Set, String)
}

/* Getting and setting the internal FMU state */
fmi2Status FMI2GetFMUstate(FMIInstance *instance, fmi2FMUstate* FMUstate) {
    CALL_ARGS(GetFMUstate, "FMUstate=0x%p", FMUstate)
}

fmi2Status FMI2SetFMUstate(FMIInstance *instance, fmi2FMUstate  FMUstate) {
    CALL_ARGS(SetFMUstate, "FMUstate=0x%p", FMUstate)
}

fmi2Status FMI2FreeFMUstate(FMIInstance *instance, fmi2FMUstate* FMUstate) {
    CALL_ARGS(FreeFMUstate, "FMUstate=0x%p", FMUstate)
}

fmi2Status FMI2SerializedFMUstateSize(FMIInstance *instance, fmi2FMUstate  FMUstate, size_t* size) {
    fmi2Status status = instance->fmi2Functions->fmi2SerializedFMUstateSize(instance->component, FMUstate, size);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2SerializedFMUstateSize(FMUstate=0x%p, size=%zu)", FMUstate, *size);
    }
    return status;
}

fmi2Status FMI2SerializeFMUstate(FMIInstance *instance, fmi2FMUstate  FMUstate, fmi2Byte serializedState[], size_t size) {
    CALL_ARGS(SerializeFMUstate, "FMUstate=0x%p, serializedState=0x%p, size=%zu", FMUstate, serializedState, size);
}

fmi2Status FMI2DeSerializeFMUstate(FMIInstance *instance, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
    CALL_ARGS(DeSerializeFMUstate, "serializedState=0x%p, size=%zu, FMUstate=0x%p", serializedState, size, FMUstate);
}

/* Getting partial derivatives */
fmi2Status FMI2GetDirectionalDerivative(FMIInstance *instance,
    const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
    const fmi2ValueReference vKnown_ref[], size_t nKnown,
    const fmi2Real dvKnown[],
    fmi2Real dvUnknown[]) {
    CALL_ARGS(GetDirectionalDerivative, "vUnknown_ref=0x%p, nUnknown=%zu, vKnown_ref=0x%p, nKnown=%zu, dvKnown=0x%p, dvUnknown=0x%p",
        vUnknown_ref, nUnknown, vKnown_ref, nKnown, dvKnown, dvUnknown)
}

/***************************************************
Model Exchange
****************************************************/

/* Enter and exit the different modes */
fmi2Status FMI2EnterEventMode(FMIInstance *instance) {
    instance->state = FMI2EventModeState;
    CALL(EnterEventMode)
}

fmi2Status FMI2NewDiscreteStates(FMIInstance *instance, fmi2EventInfo *eventInfo) {
    fmi2Status status = instance->fmi2Functions->fmi2NewDiscreteStates(instance->component, eventInfo);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi2NewDiscreteStates(eventInfo={newDiscreteStatesNeeded=%d, terminateSimulation=%d, nominalsOfContinuousStatesChanged=%d, valuesOfContinuousStatesChanged=%d, nextEventTimeDefined=%d, nextEventTime=%.16g})",
            eventInfo->newDiscreteStatesNeeded, eventInfo->terminateSimulation, eventInfo->nominalsOfContinuousStatesChanged, eventInfo->valuesOfContinuousStatesChanged, eventInfo->nextEventTimeDefined, eventInfo->nextEventTime);
    }
    return status;
}

fmi2Status FMI2EnterContinuousTimeMode(FMIInstance *instance) {
    instance->state = FMI2ContinuousTimeModeState;
    CALL(EnterContinuousTimeMode)
}

fmi2Status FMI2CompletedIntegratorStep(FMIInstance *instance,
    fmi2Boolean   noSetFMUStatePriorToCurrentPoint,
    fmi2Boolean*  enterEventMode,
    fmi2Boolean*  terminateSimulation) {
    fmi2Status status = instance->fmi2Functions->fmi2CompletedIntegratorStep(instance->component, noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2CompletedIntegratorStep(noSetFMUStatePriorToCurrentPoint=%d, enterEventMode=%d, terminateSimulation=%d)", noSetFMUStatePriorToCurrentPoint, *enterEventMode, *terminateSimulation);
    }
    return status;
}

/* Providing independent variables and re-initialization of caching */
fmi2Status FMI2SetTime(FMIInstance *instance, fmi2Real time) {
    CALL_ARGS(SetTime, "time=%.16g", time)
}

fmi2Status FMI2SetContinuousStates(FMIInstance *instance, const fmi2Real x[], size_t nx) {
    fmi2Status status = instance->fmi2Functions->fmi2SetContinuousStates(instance->component, x, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, x, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2SetContinuousStates(x=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

/* Evaluation of the model equations */
fmi2Status FMI2GetDerivatives(FMIInstance *instance, fmi2Real derivatives[], size_t nx) {
    fmi2Status status = instance->fmi2Functions->fmi2GetDerivatives(instance->component, derivatives, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, derivatives, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2GetDerivatives(derivatives=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi2Status FMI2GetEventIndicators(FMIInstance *instance, fmi2Real eventIndicators[], size_t ni) {
    fmi2Status status = instance->fmi2Functions->fmi2GetEventIndicators(instance->component, eventIndicators, ni);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, ni, eventIndicators, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2GetEventIndicators(eventIndicators=%s, ni=%zu)", instance->buf2, ni);
    }
    return status;
}

fmi2Status FMI2GetContinuousStates(FMIInstance *instance, fmi2Real x[], size_t nx) {
    fmi2Status status = instance->fmi2Functions->fmi2GetContinuousStates(instance->component, x, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, x, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2GetContinuousStates(x=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi2Status FMI2GetNominalsOfContinuousStates(FMIInstance *instance, fmi2Real x_nominal[], size_t nx) {
    fmi2Status status = instance->fmi2Functions->fmi2GetNominalsOfContinuousStates(instance->component, x_nominal, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, x_nominal, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2GetNominalsOfContinuousStates(x_nominal=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

/***************************************************
Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status FMI2SetRealInputDerivatives(FMIInstance *instance,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    const fmi2Real value[]) {
    CALL_ARGS(SetRealInputDerivatives, "vr=0x%p, nvr=%zu, order=0x%p, value=0x%p", vr, nvr, order, value);
}

fmi2Status FMI2GetRealOutputDerivatives(FMIInstance *instance,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    fmi2Real value[]) {
    CALL_ARGS(GetRealOutputDerivatives, "vr=0x%p, nvr=%zu, order=0x%p, value=0x%p", vr, nvr, order, value)
}

fmi2Status FMI2DoStep(FMIInstance *instance,
    fmi2Real      currentCommunicationPoint,
    fmi2Real      communicationStepSize,
    fmi2Boolean   noSetFMUStatePriorToCurrentPoint) {

    instance->time = currentCommunicationPoint + communicationStepSize;

    CALL_ARGS(DoStep, "currentCommunicationPoint=%.16g, communicationStepSize=%.16g, noSetFMUStatePriorToCurrentPoint=%d",
        currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint)
}

fmi2Status FMI2CancelStep(FMIInstance *instance) {
    CALL(CancelStep);
}

/* Inquire slave status */
fmi2Status FMI2GetStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Status* value) {
    fmi2Status status = instance->fmi2Functions->fmi2GetStatus(instance->component, s, value);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2GetStatus(s=%s, value=%d)", s, *value);
    }
    return status;
}

fmi2Status FMI2GetRealStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Real* value) {
    fmi2Status status = instance->fmi2Functions->fmi2GetRealStatus(instance->component, s, value);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2GetRealStatus(s=%s, value=%.16g)", s, *value);
    }
    return status;
}

fmi2Status FMI2GetIntegerStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Integer* value) {
    fmi2Status status = instance->fmi2Functions->fmi2GetIntegerStatus(instance->component, s, value);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2GetIntegerStatus(s=%s, value=%d)", s, *value);
    }
    return status;
}

fmi2Status FMI2GetBooleanStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Boolean* value) {
    fmi2Status status = instance->fmi2Functions->fmi2GetBooleanStatus(instance->component, s, value);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2GetBooleanStatus(s=%s, value=%d)", s, *value);
    }
    return status;
}

fmi2Status FMI2GetStringStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2String* value) {
    fmi2Status status = instance->fmi2Functions->fmi2GetStringStatus(instance->component, s, value);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi2GetStringStatus(s=%s, value=%s)", s, *value);
    }
    return status;
}

#undef LOAD_SYMBOL
#undef CALL
#undef CALL_ARGS
#undef CALL_ARRAY
