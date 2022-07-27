/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#if FMI_VERSION != 2
#error FMI_VERSION must be 2
#endif

#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>

#include "config.h"
#include "model.h"
#include "cosimulation.h"


// C-code FMUs have functions names prefixed with MODEL_IDENTIFIER_.
// Define DISABLE_PREFIX to build a binary FMU.
#ifndef DISABLE_PREFIX
#define pasteA(a,b)     a ## b
#define pasteB(a,b)    pasteA(a,b)
#define FMI2_FUNCTION_PREFIX pasteB(MODEL_IDENTIFIER, _)
#endif
#include "fmi2Functions.h"

#define ASSERT_NOT_NULL(p) \
do { \
    if (!p) { \
        logError(S, "Argument %s must not be NULL.", xstr(p)); \
        S->state = modelError; \
        return (fmi2Status)Error; \
    } \
} while (0)

#define GET_VARIABLES(T) \
do { \
    ASSERT_NOT_NULL(vr); \
    ASSERT_NOT_NULL(value); \
    size_t index = 0; \
    Status status = OK; \
    if (nvr == 0) return (fmi2Status)status; \
    if (S->isDirtyValues) { \
        Status s = calculateValues(S); \
        status = max(status, s); \
        if (status > Warning) return (fmi2Status)status; \
        S->isDirtyValues = false; \
    } \
    for (size_t i = 0; i < nvr; i++) { \
        Status s = get ## T(S, vr[i], value, &index); \
        status = max(status, s); \
        if (status > Warning) return (fmi2Status)status; \
    } \
    return (fmi2Status)status; \
} while (0)

#define SET_VARIABLES(T) \
do { \
    ASSERT_NOT_NULL(vr); \
    ASSERT_NOT_NULL(value); \
    size_t index = 0; \
    Status status = OK; \
    for (size_t i = 0; i < nvr; i++) { \
        Status s = set ## T(S, vr[i], value, &index); \
        status = max(status, s); \
        if (status > Warning) return (fmi2Status)status; \
    } \
    if (nvr > 0) S->isDirtyValues = true; \
    return (fmi2Status)status; \
} while (0)

#define GET_BOOLEAN_VARIABLES \
do { \
    Status status = OK; \
    for (size_t i = 0; i < nvr; i++) { \
        bool v = false; \
        size_t index = 0; \
        Status s = getBoolean(S, vr[i], &v, &index); \
        value[i] = v; \
        status = max(status, s); \
        if (status > Warning) return (fmi2Status)status; \
    } \
    return (fmi2Status)status; \
} while (0)

#define SET_BOOLEAN_VARIABLES \
do { \
    Status status = OK; \
    for (size_t i = 0; i < nvr; i++) { \
        bool v = value[i]; \
        size_t index = 0; \
        Status s = setBoolean(S, vr[i], &v, &index); \
        status = max(status, s); \
        if (status > Warning) return (fmi2Status)status; \
    } \
    return (fmi2Status)status; \
} while (0)

#ifndef max
#define max(a,b) ((a)>(b) ? (a) : (b))
#endif

#ifndef DT_EVENT_DETECT
#define DT_EVENT_DETECT 1e-10
#endif

// ---------------------------------------------------------------------------
// Function calls allowed state masks for both Model-exchange and Co-simulation
// ---------------------------------------------------------------------------
#define MASK_fmi2GetTypesPlatform        (StartAndEnd | Instantiated | InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete | StepInProgress | StepFailed | StepCanceled \
| Terminated | Error)
#define MASK_fmi2GetVersion              MASK_fmi2GetTypesPlatform
#define MASK_fmi2SetDebugLogging         (Instantiated | InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete | StepInProgress | StepFailed | StepCanceled \
| Terminated | Error)
#define MASK_fmi2Instantiate             (StartAndEnd)
#define MASK_fmi2FreeInstance            (Instantiated | InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete | StepFailed | StepCanceled \
| Terminated | Error)
#define MASK_fmi2SetupExperiment         Instantiated
#define MASK_fmi2EnterInitializationMode Instantiated
#define MASK_fmi2ExitInitializationMode  InitializationMode
#define MASK_fmi2Terminate               (EventMode | ContinuousTimeMode \
| StepComplete | StepFailed)
#define MASK_fmi2Reset                   MASK_fmi2FreeInstance
#define MASK_fmi2GetReal                 (InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete | StepFailed | StepCanceled \
| Terminated | Error)
#define MASK_fmi2GetInteger              MASK_fmi2GetReal
#define MASK_fmi2GetBoolean              MASK_fmi2GetReal
#define MASK_fmi2GetString               MASK_fmi2GetReal
#define MASK_fmi2SetReal                 (Instantiated | InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete)
#define MASK_fmi2SetInteger              (Instantiated | InitializationMode \
| EventMode \
| StepComplete)
#define MASK_fmi2SetBoolean              MASK_fmi2SetInteger
#define MASK_fmi2SetString               MASK_fmi2SetInteger
#define MASK_fmi2GetFMUstate             MASK_fmi2FreeInstance
#define MASK_fmi2SetFMUstate             MASK_fmi2FreeInstance
#define MASK_fmi2FreeFMUstate            MASK_fmi2FreeInstance
#define MASK_fmi2SerializedFMUstateSize  MASK_fmi2FreeInstance
#define MASK_fmi2SerializeFMUstate       MASK_fmi2FreeInstance
#define MASK_fmi2DeSerializeFMUstate     MASK_fmi2FreeInstance
#define MASK_fmi2GetDirectionalDerivative (InitializationMode \
| EventMode | ContinuousTimeMode \
| StepComplete | StepFailed | StepCanceled \
| Terminated | Error)

// ---------------------------------------------------------------------------
// Function calls allowed state masks for Model-exchange
// ---------------------------------------------------------------------------
#define MASK_fmi2EnterEventMode          (EventMode | ContinuousTimeMode)
#define MASK_fmi2NewDiscreteStates       EventMode
#define MASK_fmi2EnterContinuousTimeMode EventMode
#define MASK_fmi2CompletedIntegratorStep ContinuousTimeMode
#define MASK_fmi2SetTime                 (EventMode | ContinuousTimeMode)
#define MASK_fmi2SetContinuousStates     ContinuousTimeMode
#define MASK_fmi2GetEventIndicators      (InitializationMode \
| EventMode | ContinuousTimeMode \
| Terminated | Error)
#define MASK_fmi2GetContinuousStates     MASK_fmi2GetEventIndicators
#define MASK_fmi2GetDerivatives          (EventMode | ContinuousTimeMode \
| Terminated | Error)
#define MASK_fmi2GetNominalsOfContinuousStates ( Instantiated \
| EventMode | ContinuousTimeMode \
| Terminated | Error)

// ---------------------------------------------------------------------------
// Function calls allowed state masks for Co-simulation
// ---------------------------------------------------------------------------
#define MASK_fmi2SetRealInputDerivatives (Instantiated | InitializationMode \
| StepComplete)
#define MASK_fmi2GetRealOutputDerivatives (StepComplete | StepFailed | StepCanceled \
| Terminated | Error)
#define MASK_fmi2DoStep                  StepComplete
#define MASK_fmi2CancelStep              StepInProgress
#define MASK_fmi2GetStatus               (StepComplete | StepInProgress | StepFailed \
| Terminated)
#define MASK_fmi2GetRealStatus           MASK_fmi2GetStatus
#define MASK_fmi2GetIntegerStatus        MASK_fmi2GetStatus
#define MASK_fmi2GetBooleanStatus        MASK_fmi2GetStatus
#define MASK_fmi2GetStringStatus         MASK_fmi2GetStatus

// shorthand to access the  instance
#define S ((ModelInstance *)c)

#define ASSERT_STATE(S) \
    if (!allowedState(c, MASK_fmi2##S, #S)) \
        return fmi2Error;

static bool allowedState(ModelInstance *instance, int statesExpected, char *name) {

    if (!instance) {
        return false;
    }

    if (!(instance->state & statesExpected)) {
        logError(instance, "fmi2%s: Illegal call sequence.", name);
        return false;
    }

    return true;

}

// ---------------------------------------------------------------------------
// FMI functions
// ---------------------------------------------------------------------------

fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID,
                            fmi2String fmuResourceLocation, const fmi2CallbackFunctions *functions,
                            fmi2Boolean visible, fmi2Boolean loggingOn) {

    UNUSED(visible);

    if (!functions || !functions->logger) {
        return NULL;
    }

    return createModelInstance(
        (loggerType)functions->logger,
        NULL,
        functions->componentEnvironment,
        instanceName,
        fmuGUID,
        fmuResourceLocation,
        loggingOn,
        (InterfaceType)fmuType);
}

fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance,
                            fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) {

    UNUSED(toleranceDefined);
    UNUSED(tolerance);
    UNUSED(stopTimeDefined);
    UNUSED(stopTime);

    ASSERT_STATE(SetupExperiment)

    S->time = startTime;

    return fmi2OK;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) {

    ASSERT_STATE(EnterInitializationMode)

    S->state = InitializationMode;

    return fmi2OK;
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c) {

    ASSERT_STATE(ExitInitializationMode);

    fmi2Status status = fmi2OK;

    // if values were set and no fmi2GetXXX triggered update before,
    // ensure calculated values are updated now
    if (S->isDirtyValues) {
        status = (fmi2Status)calculateValues(S);
        S->isDirtyValues = false;
    }

    if (S->type == ModelExchange) {
        S->state = EventMode;
    } else {
        S->state = StepComplete;
    }

    return status;
}

fmi2Status fmi2Terminate(fmi2Component c) {

    ASSERT_STATE(Terminate)

    S->state = Terminated;

    return fmi2OK;
}

fmi2Status fmi2Reset(fmi2Component c) {

    ASSERT_STATE(Reset);

    reset(S);

    return fmi2OK;
}

void fmi2FreeInstance(fmi2Component c) {

    if (S) {
        freeModelInstance(S);
    }
}

// ---------------------------------------------------------------------------
// FMI functions: class methods not depending of a specific model instance
// ---------------------------------------------------------------------------

const char* fmi2GetVersion() {
    return fmi2Version;
}

const char* fmi2GetTypesPlatform() {
    return fmi2TypesPlatform;
}

// ---------------------------------------------------------------------------
// FMI functions: logging control, setters and getters for Real, Integer,
// Boolean, String
// ---------------------------------------------------------------------------

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {

    ASSERT_STATE(SetDebugLogging)

    return (fmi2Status)setDebugLogging(S, loggingOn, nCategories, categories);
}

fmi2Status fmi2GetReal (fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {

    ASSERT_STATE(GetReal)

    if (nvr > 0 && nullPointer(S, "fmi2GetReal", "vr[]", vr))
        return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2GetReal", "value[]", value))
        return fmi2Error;

    if (nvr > 0 && S->isDirtyValues) {
        calculateValues(S);
        S->isDirtyValues = false;
    }

    GET_VARIABLES(Float64);
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {

    ASSERT_STATE(GetInteger)

    if (nvr > 0 && nullPointer(S, "fmi2GetInteger", "vr[]", vr))
            return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2GetInteger", "value[]", value))
            return fmi2Error;

    if (nvr > 0 && S->isDirtyValues) {
        calculateValues(S);
        S->isDirtyValues = false;
    }

    GET_VARIABLES(Int32);
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {

    ASSERT_STATE(GetBoolean)

    if (nvr > 0 && nullPointer(S, "fmi2GetBoolean", "vr[]", vr))
            return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2GetBoolean", "value[]", value))
            return fmi2Error;

    if (nvr > 0 && S->isDirtyValues) {
        calculateValues(S);
        S->isDirtyValues = false;
    }

    GET_BOOLEAN_VARIABLES;
}

fmi2Status fmi2GetString (fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String value[]) {

    ASSERT_STATE(GetString)

    if (nvr>0 && nullPointer(S, "fmi2GetString", "vr[]", vr))
            return fmi2Error;

    if (nvr>0 && nullPointer(S, "fmi2GetString", "value[]", value))
            return fmi2Error;

    if (nvr > 0 && S->isDirtyValues) {
        calculateValues(S);
        S->isDirtyValues = false;
    }

    GET_VARIABLES(String);
}

fmi2Status fmi2SetReal (fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {

    ASSERT_STATE(SetReal)

    if (invalidState(S, "fmi2SetReal", MASK_fmi2SetReal))
        return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2SetReal", "vr[]", vr))
        return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2SetReal", "value[]", value))
        return fmi2Error;

    SET_VARIABLES(Float64);
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {

    ASSERT_STATE(SetInteger)

    if (nvr > 0 && nullPointer(S, "fmi2SetInteger", "vr[]", vr))
        return fmi2Error;

    if (nvr > 0 && nullPointer(S, "fmi2SetInteger", "value[]", value))
        return fmi2Error;

    SET_VARIABLES(Int32);
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {

    ASSERT_STATE(SetBoolean)

    if (nvr>0 && nullPointer(S, "fmi2SetBoolean", "vr[]", vr))
        return fmi2Error;

    if (nvr>0 && nullPointer(S, "fmi2SetBoolean", "value[]", value))
        return fmi2Error;

    SET_BOOLEAN_VARIABLES;
}

fmi2Status fmi2SetString (fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String value[]) {

    ASSERT_STATE(SetString);

    if (nvr>0 && nullPointer(S, "fmi2SetString", "vr[]", vr))
        return fmi2Error;

    if (nvr>0 && nullPointer(S, "fmi2SetString", "value[]", value))
        return fmi2Error;

    SET_VARIABLES(String);
}

fmi2Status fmi2GetFMUstate (fmi2Component c, fmi2FMUstate* FMUstate) {

    ASSERT_STATE(GetFMUstate);

    *FMUstate = getFMUState(S);

    return fmi2OK;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate FMUstate) {

    ASSERT_STATE(SetFMUstate);

    if (nullPointer(S, "fmi2SetFMUstate", "FMUstate", FMUstate)) {
        return fmi2Error;
    }

    setFMUState(S, FMUstate);

    return fmi2OK;
}

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {

    ASSERT_STATE(FreeFMUstate);

    free(*FMUstate);

    *FMUstate = NULL;

    return fmi2OK;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate FMUstate, size_t *size) {

    UNUSED(c);
    UNUSED(FMUstate);

    ASSERT_STATE(SerializedFMUstateSize);

    *size = sizeof(ModelInstance);

    return fmi2OK;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate FMUstate, fmi2Byte serializedState[], size_t size) {

    ASSERT_STATE(SerializeFMUstate);

    if (nullPointer(S, "fmi2SerializeFMUstate", "FMUstate", FMUstate)) {
        return fmi2Error;
    }

    if (invalidNumber(S, "fmi2SerializeFMUstate", "size", size, sizeof(ModelInstance))) {
        return fmi2Error;
    }

    memcpy(serializedState, FMUstate, sizeof(ModelInstance));

    return fmi2OK;
}

fmi2Status fmi2DeSerializeFMUstate (fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {

    ASSERT_STATE(DeSerializeFMUstate);

    if (invalidNumber(S, "fmi2DeSerializeFMUstate", "size", size, sizeof(ModelInstance))) {
        return fmi2Error;
    }

    if (*FMUstate == NULL) {
        *FMUstate = calloc(1, sizeof(ModelInstance));
    }

    memcpy(*FMUstate, serializedState, sizeof(ModelInstance));

    return fmi2OK;
}

fmi2Status fmi2GetDirectionalDerivative(fmi2Component c, const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
                                        const fmi2ValueReference vKnown_ref[] , size_t nKnown,
                                        const fmi2Real dvKnown[], fmi2Real dvUnknown[]) {

    ASSERT_STATE(GetDirectionalDerivative);

    // TODO: check value references
    // TODO: assert nUnknowns == nDeltaOfUnknowns
    // TODO: assert nKnowns == nDeltaKnowns

    Status status = OK;

    for (size_t i = 0; i < nUnknown; i++) {
        dvUnknown[i] = 0;
        for (size_t j = 0; j < nKnown; j++) {
            double partialDerivative = 0;
            Status s = getPartialDerivative(S, vUnknown_ref[i], vKnown_ref[j], &partialDerivative);
            status = max(status, s);
            if (status > Warning) {
                return (fmi2Status)status;
            }
            dvUnknown[i] += partialDerivative * dvKnown[j];
        }
    }

    return fmi2OK;
}

// ---------------------------------------------------------------------------
// Functions for FMI for Co-Simulation
// ---------------------------------------------------------------------------
/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr,
                                     const fmi2Integer order[], const fmi2Real value[]) {

    UNUSED(vr);
    UNUSED(nvr);
    UNUSED(order);
    UNUSED(value);

    ASSERT_STATE(SetRealInputDerivatives);

    logError(S, "fmi2SetRealInputDerivatives: ignoring function call."
            " This model cannot interpolate inputs: canInterpolateInputs=\"fmi2False\"");

    return fmi2Error;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr,
                                      const fmi2Integer order[], fmi2Real value[]) {

    ASSERT_STATE(GetRealOutputDerivatives);

#ifdef GET_OUTPUT_DERIVATIVE
    Status status = OK;

    for (size_t i = 0; i < nvr; i++) {
        const Status s = getOutputDerivative(S, vr[i], order[i], &value[i]);
        status = max(status, s);
        if (status > Warning) {
            return (fmi2Status)status;
        }
    }

    return (fmi2Status)status;
#else
    UNUSED(vr);
    UNUSED(nvr);
    UNUSED(order);
    UNUSED(value);

    logError(S, "fmi2GetRealOutputDerivatives: ignoring function call."
        " This model cannot compute derivatives of outputs: MaxOutputDerivativeOrder=\"0\"");

    return fmi2Error;
#endif
}

fmi2Status fmi2CancelStep(fmi2Component c) {

    ASSERT_STATE(CancelStep);

    logError(S, "fmi2CancelStep: Can be called when fmi2DoStep returned fmi2Pending."
        " This is not the case.");

    return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint,
                    fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {

    UNUSED(noSetFMUStatePriorToCurrentPoint);

    ASSERT_STATE(DoStep);

    if (communicationStepSize <= 0) {
        logError(S, "fmi2DoStep: communication step size must be > 0 but was %g.", communicationStepSize);
        S->state = modelError;
        return fmi2Error;
    }

    const fmi2Real nextCommunicationPoint = currentCommunicationPoint + communicationStepSize + EPSILON;

    while (true) {

        if (S->time + FIXED_SOLVER_STEP > nextCommunicationPoint) {
            break;  // next communcation point reached
        }

        bool stateEvent, timeEvent;

        doFixedStep(S, &stateEvent, &timeEvent);

#ifdef EVENT_UPDATE
        if (stateEvent || timeEvent) {
            eventUpdate(S);
        }
#endif
    }

    return S->terminateSimulation ? fmi2Discard : fmi2OK;
}

/* Inquire slave status */
static fmi2Status getStatus(char* fname, fmi2Component c, const fmi2StatusKind s) {

    if (invalidState(S, fname, MASK_fmi2GetStatus)) // all get status have the same MASK_fmi2GetStatus
        return fmi2Error;

    switch(s) {
    case fmi2DoStepStatus: logError(S,
        "%s: Can be called with fmi2DoStepStatus when fmi2DoStep returned fmi2Pending."
        " This is not the case.", fname);
        break;
    case fmi2PendingStatus: logError(S,
        "%s: Can be called with fmi2PendingStatus when fmi2DoStep returned fmi2Pending."
        " This is not the case.", fname);
        break;
    case fmi2LastSuccessfulTime: logError(S,
        "%s: Can be called with fmi2LastSuccessfulTime when fmi2DoStep returned fmi2Discard."
        " This is not the case.", fname);
        break;
    case fmi2Terminated: logError(S,
        "%s: Can be called with fmi2Terminated when fmi2DoStep returned fmi2Discard."
        " This is not the case.", fname);
        break;
    }

    return fmi2Discard;
}

fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status *value) {

    UNUSED(value);

    ASSERT_STATE(GetStatus);

    return getStatus("fmi2GetStatus", c, s);
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real *value) {

    ASSERT_STATE(GetRealStatus);

    if (s == fmi2LastSuccessfulTime) {
        *value = S->time;
        return fmi2OK;
    }

    return getStatus("fmi2GetRealStatus", c, s);
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer *value) {

    UNUSED(value);

    ASSERT_STATE(GetIntegerStatus);

    return getStatus("fmi2GetIntegerStatus", c, s);
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean *value) {

    ASSERT_STATE(GetBooleanStatus);

    if (s == fmi2Terminated) {
        *value = S->terminateSimulation;
        return fmi2OK;
    }

    return getStatus("fmi2GetBooleanStatus", c, s);
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String *value) {
    UNUSED(value);
    ASSERT_STATE(GetStringStatus);
    return getStatus("fmi2GetStringStatus", c, s);
}

// ---------------------------------------------------------------------------
// Functions for FMI2 for Model Exchange
// ---------------------------------------------------------------------------
/* Enter and exit the different modes */
fmi2Status fmi2EnterEventMode(fmi2Component c) {

    ASSERT_STATE(EnterEventMode);

    S->state = EventMode;

    return fmi2OK;
}

fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo *eventInfo) {

    ASSERT_STATE(NewDiscreteStates);

#ifdef EVENT_UPDATE
    eventUpdate(S);
#endif

    eventInfo->newDiscreteStatesNeeded           = S->newDiscreteStatesNeeded;
    eventInfo->terminateSimulation               = S->terminateSimulation;
    eventInfo->nominalsOfContinuousStatesChanged = S->nominalsOfContinuousStatesChanged;
    eventInfo->valuesOfContinuousStatesChanged   = S->valuesOfContinuousStatesChanged;
    eventInfo->nextEventTimeDefined              = S->nextEventTimeDefined;
    eventInfo->nextEventTime                     = S->nextEventTime;

    return fmi2OK;
}

fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {

    ASSERT_STATE(EnterContinuousTimeMode);

    S->state = ContinuousTimeMode;

    return fmi2OK;
}

fmi2Status fmi2CompletedIntegratorStep(fmi2Component c, fmi2Boolean noSetFMUStatePriorToCurrentPoint,
                                     fmi2Boolean *enterEventMode, fmi2Boolean *terminateSimulation) {



    UNUSED(noSetFMUStatePriorToCurrentPoint);

    ASSERT_STATE(CompletedIntegratorStep);

    if (nullPointer(S, "fmi2CompletedIntegratorStep", "enterEventMode", enterEventMode))
        return fmi2Error;

    if (nullPointer(S, "fmi2CompletedIntegratorStep", "terminateSimulation", terminateSimulation))
        return fmi2Error;

    *enterEventMode = fmi2False;
    *terminateSimulation = fmi2False;

    return fmi2OK;
}

/* Providing independent variables and re-initialization of caching */
fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {

    ASSERT_STATE(SetTime);

    S->time = time;

    return fmi2OK;
}

fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx){

    ASSERT_STATE(SetContinuousStates);

    if (invalidNumber(S, "fmi2SetContinuousStates", "nx", nx, NX))
        return fmi2Error;

    if (nullPointer(S, "fmi2SetContinuousStates", "x[]", x))
        return fmi2Error;

    setContinuousStates(S, x, nx);

    return fmi2OK;
}

/* Evaluation of the model equations */
fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {

    ASSERT_STATE(GetDerivatives);

    if (invalidNumber(S, "fmi2GetDerivatives", "nx", nx, NX))
        return fmi2Error;

    if (nullPointer(S, "fmi2GetDerivatives", "derivatives[]", derivatives))
        return fmi2Error;

    getDerivatives(S, derivatives, nx);

    return fmi2OK;
}

fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {

    ASSERT_STATE(GetEventIndicators);

#if NZ > 0

    if (invalidNumber(S, "fmi2GetEventIndicators", "ni", ni, NZ))
        return fmi2Error;

    getEventIndicators(S, eventIndicators, ni);
#else
    UNUSED(c);
    UNUSED(eventIndicators);
    if (ni > 0) return fmi2Error;
#endif
    return fmi2OK;
}

fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real states[], size_t nx) {

    ASSERT_STATE(GetContinuousStates);

    if (invalidNumber(S, "fmi2GetContinuousStates", "nx", nx, NX))
        return fmi2Error;

    if (nullPointer(S, "fmi2GetContinuousStates", "states[]", states))
        return fmi2Error;

    getContinuousStates(S, states, nx);

    return fmi2OK;
}

fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {

    ASSERT_STATE(GetNominalsOfContinuousStates);

    if (invalidNumber(S, "fmi2GetNominalContinuousStates", "nx", nx, NX))
        return fmi2Error;

    if (nullPointer(S, "fmi2GetNominalContinuousStates", "x_nominal[]", x_nominal))
        return fmi2Error;

    for (size_t i = 0; i < nx; i++)
        x_nominal[i] = 1;

    return fmi2OK;
}
