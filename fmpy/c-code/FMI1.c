/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#include <stdio.h>
#include <string.h>
#include <stdarg.h>

#ifndef _WIN32
#include <dlfcn.h>
#endif

#include "FMI1.h"


// keep track of the current instance for the log callback
static FMIInstance *currentInstance = NULL;

static void cb_logMessage1(fmi1Component c, fmi1String instanceName, fmi1Status status, fmi1String category, fmi1String message, ...) {

    if (!currentInstance) return;

    char buf[FMI_MAX_MESSAGE_LENGTH];

    va_list args;

    va_start(args, message);
    vsnprintf(buf, FMI_MAX_MESSAGE_LENGTH, message, args);
    va_end(args);

    if (!currentInstance->logMessage) return;

    currentInstance->logMessage(currentInstance, status, category, buf);
}

#define MAX_SYMBOL_LENGTH 256

static void *loadSymbol(FMIInstance *instance, const char *prefix, const char *name) {
    char fname[MAX_SYMBOL_LENGTH];
    strcpy(fname, prefix);
    strcat(fname, name);
#ifdef _WIN32
    void *addr = GetProcAddress(instance->libraryHandle, fname);
#else
    void *addr = dlsym(instance->libraryHandle, fname);
#endif
    if (!addr) {
        instance->logFunctionCall(instance, FMIError, "Failed to load function \"%s\".", fname);
    }
    return addr;
}

#define LOAD_SYMBOL(f) \
    instance->fmi1Functions->fmi1 ## f = (fmi1 ## f ## TYPE*)loadSymbol(instance, modelIdentifier, "_fmi" #f); \
    if (!instance->fmi1Functions->fmi1 ## f) { \
        status = fmi1Error; \
        goto fail; \
    }

#define CALL(f) \
    currentInstance = instance; \
    fmi1Status status = instance->fmi1Functions->fmi1 ## f (instance->component); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi" #f "()"); \
    } \
    return status;

#define CALL_ARGS(f, m, ...) \
    currentInstance = instance; \
    fmi1Status status = instance->fmi1Functions->fmi1 ## f (instance->component, __VA_ARGS__); \
    if (instance->logFunctionCall) { \
        instance->logFunctionCall(instance, status, "fmi" #f "(" m ")", __VA_ARGS__); \
    } \
    return status;

#define CALL_ARRAY(s, t) \
    currentInstance = instance; \
    fmi1Status status = instance->fmi1Functions->fmi1 ## s ## t(instance->component, vr, nvr, value); \
    if (instance->logFunctionCall) { \
        FMIValueReferencesToString(instance, vr, nvr); \
        FMIValuesToString(instance, nvr, value, FMI ## t ## Type); \
        instance->logFunctionCall(instance, status, "fmi" #s #t "(vr=%s, nvr=%zu, value=%s)", instance->buf1, nvr, instance->buf2); \
    } \
    return status;

/***************************************************
 Common Functions for FMI 1.0
****************************************************/

fmi1Status    FMI1SetReal(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Real    value[]) {
    CALL_ARRAY(Set, Real)
}

fmi1Status    FMI1SetInteger(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer value[]) {
    CALL_ARRAY(Set, Integer)
}

fmi1Status    FMI1SetBoolean(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Boolean value[]) {
    CALL_ARRAY(Set, Boolean)
}

fmi1Status    FMI1SetString(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1String  value[]) {
    CALL_ARRAY(Set, String)
}

fmi1Status    FMI1GetReal(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, fmi1Real    value[]) {
    CALL_ARRAY(Get, Real)
}

fmi1Status    FMI1GetInteger(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, fmi1Integer value[]) {
    CALL_ARRAY(Get, Integer)
}

fmi1Status    FMI1GetBoolean(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, fmi1Boolean value[]) {
    CALL_ARRAY(Get, Boolean)
}

fmi1Status    FMI1GetString(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, fmi1String  value[]) {
    CALL_ARRAY(Get, String)
}

fmi1Status    FMI1SetDebugLogging(FMIInstance *instance, fmi1Boolean loggingOn) {
    CALL_ARGS(SetDebugLogging, "loggingOn=%d", loggingOn)
}


/***************************************************
 FMI 1.0 for Model Exchange Functions
****************************************************/

const char*   FMI1GetModelTypesPlatform(FMIInstance *instance) {
    currentInstance = instance;
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmiGetModelTypesPlatform()");
    }
    return instance->fmi1Functions->fmi1GetModelTypesPlatform();
}

const char*   FMI1GetVersion(FMIInstance *instance) {
    currentInstance = instance;
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmiGetVersion()");
    }
    return instance->fmi1Functions->fmi1GetVersion();
}

fmi1Status FMI1InstantiateModel(FMIInstance *instance, fmi1String modelIdentifier, fmi1String GUID, fmi1Boolean loggingOn) {

    currentInstance = instance;

    instance->fmiVersion = FMIVersion1;

    fmi1Status status = fmi1OK;

    instance->fmi1Functions = calloc(1, sizeof(FMI1Functions));

    if (!instance->fmi1Functions) {
        return fmi1Error;
    }

    /***************************************************
     Common Functions for FMI 1.0
    ****************************************************/
    LOAD_SYMBOL(SetReal)
    LOAD_SYMBOL(SetInteger)
    LOAD_SYMBOL(SetBoolean)
    LOAD_SYMBOL(SetString)
    LOAD_SYMBOL(GetReal)
    LOAD_SYMBOL(GetInteger)
    LOAD_SYMBOL(GetBoolean)
    LOAD_SYMBOL(GetString)
    LOAD_SYMBOL(SetDebugLogging)

    /***************************************************
        FMI 1.0 for Model Exchange Functions
    ****************************************************/
    LOAD_SYMBOL(GetModelTypesPlatform)
    LOAD_SYMBOL(GetVersion)
    LOAD_SYMBOL(InstantiateModel)
    LOAD_SYMBOL(FreeModelInstance)
    LOAD_SYMBOL(SetTime)
    LOAD_SYMBOL(SetContinuousStates)
    LOAD_SYMBOL(CompletedIntegratorStep)
    LOAD_SYMBOL(Initialize)
    LOAD_SYMBOL(GetDerivatives)
    LOAD_SYMBOL(GetEventIndicators)
    LOAD_SYMBOL(EventUpdate)
    LOAD_SYMBOL(GetContinuousStates)
    LOAD_SYMBOL(GetNominalContinuousStates)
    LOAD_SYMBOL(GetStateValueReferences)
    LOAD_SYMBOL(Terminate)

    instance->fmi1Functions->callbacks.logger         = cb_logMessage1;
    instance->fmi1Functions->callbacks.allocateMemory = calloc;
    instance->fmi1Functions->callbacks.freeMemory     = free;
    instance->fmi1Functions->callbacks.stepFinished   = NULL;

    instance->component = instance->fmi1Functions->fmi1InstantiateModel(instance->name, GUID, instance->fmi1Functions->callbacks, loggingOn);

    status = instance->component ? fmi1OK : fmi1Error;

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi1InstantiateModel(instanceName=\"%s\", GUID=\"%s\", functions=0x%p, loggingOn=%d)",
            instance->name, GUID, &instance->fmi1Functions->callbacks, loggingOn);
    }

fail:
    return status;
}

void FMI1FreeModelInstance(FMIInstance *instance) {

    currentInstance = instance;

    instance->fmi1Functions->fmi1FreeModelInstance(instance->component);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi1FreeModelInstance()");
    }
}

fmi1Status    FMI1SetTime(FMIInstance *instance, fmi1Real time) {
    CALL_ARGS(SetTime, "time=%.16g", time)
}

fmi1Status    FMI1SetContinuousStates(FMIInstance *instance, const fmi1Real x[], size_t nx) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1SetContinuousStates(instance->component, x, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, x, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi1SetContinuousStates(x=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi1Status    FMI1CompletedIntegratorStep(FMIInstance *instance, fmi1Boolean* callEventUpdate) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1CompletedIntegratorStep(instance->component, callEventUpdate);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status, "fmi1CompletedIntegratorStep(callEventUpdate=%d)", *callEventUpdate);
    }
    return status;
}

fmi1Status    FMI1Initialize(FMIInstance *instance, fmi1Boolean toleranceControlled, fmi1Real relativeTolerance) {
    fmi1EventInfo *e = &instance->fmi1Functions->eventInfo;
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1Initialize(instance->component, toleranceControlled, relativeTolerance, e);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi1Initialize(toleranceControlled=%d, relativeTolerance=%.16g, eventInfo={iterationConverged=%d, stateValueReferencesChanged=%d, stateValuesChanged=%d, terminateSimulation=%d, upcomingTimeEvent=%d, nextEventTime=%.16g})",
            toleranceControlled, relativeTolerance, e->iterationConverged, e->stateValueReferencesChanged, e->stateValuesChanged, e->terminateSimulation, e->upcomingTimeEvent, e->nextEventTime);
    }
    return status;


}

fmi1Status    FMI1GetDerivatives(FMIInstance *instance, fmi1Real derivatives[], size_t nx) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1GetDerivatives(instance->component, derivatives, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, derivatives, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi1GetDerivatives(derivatives=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi1Status    FMI1GetEventIndicators(FMIInstance *instance, fmi1Real eventIndicators[], size_t ni) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1GetEventIndicators(instance->component, eventIndicators, ni);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, ni, eventIndicators, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi1GetEventIndicators(eventIndicators=%s, ni=%zu)", instance->buf2, ni);
    }
    return status;
}

fmi1Status    FMI1EventUpdate(FMIInstance *instance, fmi1Boolean intermediateResults, fmi1EventInfo* eventInfo) {
    fmi1EventInfo *e = &instance->fmi1Functions->eventInfo;
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1EventUpdate(instance->component, intermediateResults, e);
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi1Initialize(intermediateResults=%d, eventInfo={iterationConverged=%d, stateValueReferencesChanged=%d, stateValuesChanged=%d, terminateSimulation=%d, upcomingTimeEvent=%d, nextEventTime=%.16g})",
            intermediateResults, e->iterationConverged, e->stateValueReferencesChanged, e->stateValuesChanged, e->terminateSimulation, e->upcomingTimeEvent, e->nextEventTime);
    }
    return status;
}

fmi1Status    FMI1GetContinuousStates(FMIInstance *instance, fmi1Real states[], size_t nx) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1GetContinuousStates(instance->component, states, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, states, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi2GetContinuousStates(x=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi1Status    FMI1GetNominalContinuousStates(FMIInstance *instance, fmi1Real x_nominal[], size_t nx) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1GetNominalContinuousStates(instance->component, x_nominal, nx);
    if (instance->logFunctionCall) {
        FMIValuesToString(instance, nx, x_nominal, FMIRealType);
        instance->logFunctionCall(instance, status, "fmi1GetNominalContinuousStates(x_nominal=%s, nx=%zu)", instance->buf2, nx);
    }
    return status;
}

fmi1Status    FMI1GetStateValueReferences(FMIInstance *instance, fmi1ValueReference vrx[], size_t nx) {
    currentInstance = instance;
    fmi1Status status = instance->fmi1Functions->fmi1GetStateValueReferences(instance->component, vrx, nx);
    if (instance->logFunctionCall) {
        // TODO
    }
    return status;
}

fmi1Status FMI1Terminate(FMIInstance *instance) {
    CALL(Terminate)
}

/***************************************************
 FMI 1.0 for Co-Simulation Functions
****************************************************/

const char*   FMI1GetTypesPlatform(FMIInstance *instance) {
    currentInstance = instance;
    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi1GetTypesPlatform()");
    }
    return instance->fmi1Functions->fmi1GetTypesPlatform();
}

fmi1Status FMI1InstantiateSlave(FMIInstance *instance, fmi1String modelIdentifier, fmi1String fmuGUID, fmi1String fmuLocation, fmi1String  mimeType, fmi1Real timeout, fmi1Boolean visible, fmi1Boolean interactive, fmi1Boolean loggingOn) {

    currentInstance = instance;

    instance->fmiVersion = FMIVersion1;

    fmi1Status status = fmi1OK;

    instance->fmi1Functions = calloc(1, sizeof(FMI1Functions));

    if (!instance->fmi1Functions) {
        return fmi1Error;
    }

    /***************************************************
     Common Functions for FMI 1.0
    ****************************************************/
    LOAD_SYMBOL(SetReal)
    LOAD_SYMBOL(SetInteger)
    LOAD_SYMBOL(SetBoolean)
    LOAD_SYMBOL(SetString)
    LOAD_SYMBOL(GetReal)
    LOAD_SYMBOL(GetInteger)
    LOAD_SYMBOL(GetBoolean)
    LOAD_SYMBOL(GetString)
    LOAD_SYMBOL(SetDebugLogging)

    /***************************************************
     FMI 1.0 for Co-Simulation Functions
    ****************************************************/
    LOAD_SYMBOL(GetTypesPlatform)
    LOAD_SYMBOL(InstantiateSlave)
    LOAD_SYMBOL(InitializeSlave)
    LOAD_SYMBOL(TerminateSlave)
    LOAD_SYMBOL(ResetSlave)
    LOAD_SYMBOL(FreeSlaveInstance)
    LOAD_SYMBOL(SetRealInputDerivatives)
    LOAD_SYMBOL(GetRealOutputDerivatives)
    LOAD_SYMBOL(CancelStep)
    LOAD_SYMBOL(DoStep)
    LOAD_SYMBOL(GetStatus)
    LOAD_SYMBOL(GetRealStatus)
    LOAD_SYMBOL(GetIntegerStatus)
    LOAD_SYMBOL(GetBooleanStatus)
    LOAD_SYMBOL(GetStringStatus)

    instance->fmi1Functions->callbacks.logger         = cb_logMessage1;
    instance->fmi1Functions->callbacks.allocateMemory = calloc;
    instance->fmi1Functions->callbacks.freeMemory     = free;
    instance->fmi1Functions->callbacks.stepFinished   = NULL;

    instance->component = instance->fmi1Functions->fmi1InstantiateSlave(instance->name, fmuGUID, fmuLocation, mimeType, timeout, visible, interactive, instance->fmi1Functions->callbacks, loggingOn);

    status = instance->component ? fmi1OK : fmi1Error;

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, status,
            "fmi1InstantiateSlave(instanceName=\"%s\", fmuGUID=\"%s\", fmuLocation=\"%s\", mimeType=\"%s\", timeout=%.16g, visible=%d, interactive=%d, functions=0x%p, loggingOn=%d)",
            instance->name, fmuGUID, fmuLocation, mimeType, timeout, visible, interactive, &instance->fmi1Functions->callbacks, loggingOn);
    }

fail:
    return status;
}

fmi1Status    FMI1InitializeSlave(FMIInstance *instance, fmi1Real tStart, fmi1Boolean stopTimeDefined, fmi1Real tStop) {
    CALL_ARGS(InitializeSlave, "tStart=%.16g, stopTimeDefined=%d, tStop=%.16g", tStart, stopTimeDefined, tStop);
}

fmi1Status    FMI1TerminateSlave(FMIInstance *instance) {
    CALL(TerminateSlave)
}

fmi1Status    FMI1ResetSlave(FMIInstance *instance) {
    CALL(ResetSlave)
}

void FMI1FreeSlaveInstance(FMIInstance *instance) {

    currentInstance = instance;

    instance->fmi1Functions->fmi1FreeSlaveInstance(instance->component);

    if (instance->logFunctionCall) {
        instance->logFunctionCall(instance, FMIOK, "fmi1FreeSlaveInstance()");
    }
}

fmi1Status    FMI1SetRealInputDerivatives(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer order[], const fmi1Real value[]) {
    CALL_ARGS(SetRealInputDerivatives, "vr=0x%p, nvr=%zu, order=0x%p, value=0x%p", vr, nvr, order, value);
}

fmi1Status    FMI1GetRealOutputDerivatives(FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer order[], fmi1Real value[]) {
    CALL_ARGS(GetRealOutputDerivatives, "vr=0x%p, nvr=%zu, order=0x%p, value=0x%p", vr, nvr, order, value)
}

fmi1Status    FMI1CancelStep(FMIInstance *instance) {
    CALL(CancelStep)
}

fmi1Status    FMI1DoStep(FMIInstance *instance, fmi1Real currentCommunicationPoint, fmi1Real communicationStepSize, fmi1Boolean newStep) {

    currentInstance = instance;

    instance->time = currentCommunicationPoint + communicationStepSize;

    CALL_ARGS(DoStep, "currentCommunicationPoint=%.16g, communicationStepSize=%.16g, newStep=%d",
        currentCommunicationPoint, communicationStepSize, newStep)
}

fmi1Status FMI1GetStatus(FMIInstance *instance, const fmi1StatusKind s, fmi1Status* value) {
    CALL_ARGS(GetStatus, "s=%d, value=0x%p", s, value)
}

fmi1Status FMI1GetRealStatus(FMIInstance *instance, const fmi1StatusKind s, fmi1Real* value) {
    CALL_ARGS(GetRealStatus, "s=%d, value=0x%p", s, value)
}

fmi1Status FMI1GetIntegerStatus(FMIInstance *instance, const fmi1StatusKind s, fmi1Integer* value) {
    CALL_ARGS(GetIntegerStatus, "s=%d, value=0x%p", s, value)
}

fmi1Status FMI1GetBooleanStatus(FMIInstance *instance, const fmi1StatusKind s, fmi1Boolean* value) {
    CALL_ARGS(GetBooleanStatus, "s=%d, value=0x%p", s, value)
}

fmi1Status FMI1GetStringStatus(FMIInstance *instance, const fmi1StatusKind s, fmi1String* value) {
    CALL_ARGS(GetStringStatus, "s=%d, value=0x%p", s, value)
}

#undef LOAD_SYMBOL
#undef CALL
#undef CALL_ARGS
#undef CALL_ARRAY
