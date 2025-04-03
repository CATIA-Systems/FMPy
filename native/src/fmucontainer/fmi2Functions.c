#include "FMI2.h"
#include "FMUContainer.h"


#define GET_SYSTEM \
    FMIStatus status = FMIOK; \
    System *s = (System *)c; \
    if (!s) return fmi2Error

#define CHECK_STATUS(S) status = S; if (status > FMIWarning) goto END

#define NOT_IMPLEMENTED \
    /*if (c) { \
        System *system = (System *)c; \
         system->logger(system->envrionment, system->instanceName, fmi2Error, "fmi2Error", "Function is not implemented."); \
    } */ \
    return fmi2Error

/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
const char* fmi2GetTypesPlatform() {
    return fmi2TypesPlatform;
}

const char* fmi2GetVersion() {
    return fmi2Version;
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        CHECK_STATUS(FMI2SetDebugLogging(m, loggingOn, nCategories, categories));
    }

END:
    return status;
}

/* Creation and destruction of FMU instances and setting debug status */
fmi2Component fmi2Instantiate(fmi2String instanceName,
    fmi2Type fmuType,
    fmi2String fmuGUID,
    fmi2String fmuResourceLocation,
    const fmi2CallbackFunctions* functions,
    fmi2Boolean visible,
    fmi2Boolean loggingOn) {

    if (!functions || !functions->logger) {
        return NULL;
    }

    if (fmuType != fmi2CoSimulation) {
        functions->logger(NULL, instanceName, fmi2Error, "logError", "Argument fmuType must be fmi2CoSimulation.");
        return NULL;
    }

    char resourcesDir[4096] = "";

    FMIURIToPath(fmuResourceLocation, resourcesDir, 4096);

    return instantiateSystem(FMIVersion2, resourcesDir, instanceName, functions->logger, functions->componentEnvironment, loggingOn, visible);
}

void fmi2FreeInstance(fmi2Component c) {

    if (c) {
        freeSystem((System*)c);
    }
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status fmi2SetupExperiment(fmi2Component c,
    fmi2Boolean toleranceDefined,
    fmi2Real tolerance,
    fmi2Real startTime,
    fmi2Boolean stopTimeDefined,
    fmi2Real stopTime) {

    GET_SYSTEM;

    s->time = startTime;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        CHECK_STATUS(FMI2SetupExperiment(m, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime));
    }

END:
    return status;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) {

    GET_SYSTEM;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        CHECK_STATUS(FMI2EnterInitializationMode(m));
    }

END:
    return status;
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c) {

    GET_SYSTEM;

    for (size_t i = 0; i < s->nComponents; i++) {

        Component* c = s->components[i];
        FMIInstance* m = c->instance;

        CHECK_STATUS(FMI2ExitInitializationMode(m));
    }

END:
    return status;
}

fmi2Status fmi2Terminate(fmi2Component c) {

    GET_SYSTEM;

    return terminateSystem(s);
}

fmi2Status fmi2Reset(fmi2Component c) {

    GET_SYSTEM;

    return resetSystem(s);
}

/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0) {
            value[i] = s->time;
            continue;
        }

        if (vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        FMIInstance* m = s->components[vm->ci[0]]->instance;

        CHECK_STATUS(FMI2GetReal(m, &(vm->vr[0]), 1, &value[i]));
    }
END:
    return status;
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }
        
        const VariableMapping* vm = &s->variables[vr[i] - 1];
        FMIInstance* m = s->components[vm->ci[0]]->instance;
        
        CHECK_STATUS(FMI2GetInteger(m, &(vm->vr[0]), 1, &value[i]));
    }
END:
    return status;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        FMIInstance* m = s->components[vm->ci[0]]->instance;

        CHECK_STATUS(FMI2GetBoolean(m, &(vm->vr[0]), 1, &value[i]));
    }
END:
    return status;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        FMIInstance* m = s->components[vm->ci[0]]->instance;

        CHECK_STATUS(FMI2GetString(m, &(vm->vr[0]), 1, &value[i]));
    }
END:
    return status;
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        
        for (size_t j = 0; j < vm->size; j++) {
            FMIInstance* m = s->components[vm->ci[j]]->instance;
            CHECK_STATUS(FMI2SetReal(m, &(vm->vr[j]), 1, &value[i]));
        }
    }
END:
    return status;
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {
        
        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        
        for (size_t j = 0; j < vm->size; j++) {
            FMIInstance* m = s->components[vm->ci[j]]->instance;
            CHECK_STATUS(FMI2SetInteger(m, &(vm->vr[j]), 1, &value[i]));
        }
    }
END:
    return status;
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }

        const VariableMapping* vm = &s->variables[vr[i] - 1];
        
        for (size_t j = 0; j < vm->size; j++) {
            FMIInstance* m = s->components[vm->ci[j]]->instance;
            CHECK_STATUS(FMI2SetBoolean(m, &(vm->vr[j]), 1, &value[i]));
        }
    }
END:
    return status;
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]) {

    GET_SYSTEM;

    for (size_t i = 0; i < nvr; i++) {

        if (vr[i] == 0 || vr[i] > s->nVariables) {
            return fmi2Error;
        }
        
        const VariableMapping* vm = &s->variables[vr[i] - 1];
        for (size_t j = 0; j < vm->size; j++) {
            FMIInstance* m = s->components[vm->ci[j]]->instance;
            CHECK_STATUS(FMI2SetString(m, &(vm->vr[j]), 1, &value[i]));
        }
    }
END:
    return status;
}

/* Getting and setting the internal FMU state */
fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t* size) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte serializedState[], size_t size) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
    NOT_IMPLEMENTED;
}

/* Getting partial derivatives */
fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
    const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
    const fmi2ValueReference vKnown_ref[], size_t nKnown,
    const fmi2Real dvKnown[],
    fmi2Real dvUnknown[]) {
    NOT_IMPLEMENTED;
}

/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    const fmi2Real value[]) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    fmi2Real value[]) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2DoStep(fmi2Component c,
    fmi2Real      currentCommunicationPoint,
    fmi2Real      communicationStepSize,
    fmi2Boolean   noSetFMUStatePriorToCurrentPoint) {

    GET_SYSTEM;

    return doStep(s, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint);;
}

fmi2Status fmi2CancelStep(fmi2Component c) {
    NOT_IMPLEMENTED;
}

/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
    NOT_IMPLEMENTED;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String* value) {
    NOT_IMPLEMENTED;
}
