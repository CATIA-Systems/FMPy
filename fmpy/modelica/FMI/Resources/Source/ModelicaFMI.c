#include <stdio.h>

#include "ModelicaFMI.h"
#include "ModelicaUtilities.h"
#include "FMI2.h"


#define CALL(f) do { if (f > FMIWarning) { ModelicaFormatError("The FMU reported an error."); } } while (0)


static void logMessage(FMIInstance* instance, FMIStatus status, const char* category, const char* message) {

    switch (status) {
    case FMIOK:
        printf("[OK] ");
        break;
    case FMIWarning:
        printf("[Warning] ");
        break;
    case FMIDiscard:
        printf("[Discard] ");
        break;
    case FMIError:
        printf("[Error] ");
        break;
    case FMIFatal:
        printf("[Fatal] ");
        break;
    case FMIPending:
        printf("[Pending] ");
        break;
    }

    puts(message);
}

static void logFunctionCall(FMIInstance* instance, FMIStatus status, const char* message, ...) {

    //if (!logFile) {
    //    return;
    //}

    va_list args;
    va_start(args, message);

    //vfprintf(logFile, message, args);

    ModelicaVFormatMessage(message, args);

    switch (status) {
    case FMIOK:
        ModelicaFormatMessage(" -> OK\n");
        break;
    case FMIWarning:
        ModelicaFormatMessage(" -> Warning\n");
        break;
    case FMIDiscard:
        ModelicaFormatMessage(" -> Discard\n");
        break;
    case FMIError:
        ModelicaFormatMessage(" -> Error\n");
        break;
    case FMIFatal:
        ModelicaFormatMessage(" -> Fatal\n");
        break;
    case FMIPending:
        ModelicaFormatMessage(" -> Pending\n");
        break;
    default:
        ModelicaFormatMessage(" -> Unknown status (%d)\n", status);
        break;
    }

    va_end(args);
}

/***************************************************
Common Functions
****************************************************/

void* FMU_load(ModelicaUtilityFunctions_t* callbacks, const char* unzipdir, const char* modelIdentifier, int interfaceType, const char* instantiationToken, int visible, int loggingOn) {

    setModelicaUtilityFunctions(callbacks);

    char platformBinaryPath[2048] = "";

    FMIPlatformBinaryPath(unzipdir, modelIdentifier, FMIVersion2, platformBinaryPath, 2048);

    FMIInstance* S = FMICreateInstance("instance1", platformBinaryPath, logMessage, logFunctionCall);

    if (!S) {
        ModelicaFormatError("Failed to load platform binary %s.", platformBinaryPath);
    }

    char resourceURI[2048] = "";

    FMIPathToURI(unzipdir, resourceURI, 2048);

    if (FMI2Instantiate(S, resourceURI, (fmi2Type)interfaceType, instantiationToken, visible, loggingOn) > fmi2OK) {
        ModelicaFormatError("Failed to instantiate FMU.", platformBinaryPath);
    }
	
	return S;
}

void FMU_free(void* instance) {
    FMIInstance* S = (FMIInstance*)instance;
    FMIFreeInstance(S);
}

void FMU_FMI2GetReal(void* instance, const int vr[], int nvr, double value[]) {
    CALL(FMI2GetReal((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2GetRealScalar(void* instance, int vr, double* value) {
    CALL(FMI2GetReal((FMIInstance*)instance, &vr, 1, value));
}

void FMU_FMI2GetIntegerScalar(void* instance, int vr, int* value) {
    CALL(FMI2GetInteger((FMIInstance*)instance, &vr, 1, value));
}

void FMU_FMI2GetBooleanScalar(void* instance, int vr, int* value) {
    CALL(FMI2GetBoolean((FMIInstance*)instance, &vr, 1, value));
}

void FMU_FMI2SetReal(void* instance, const int vr[], int nvr, const double value[]) {
    CALL(FMI2SetReal((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetInteger(void* instance, const int vr[], int nvr, const int value[]) {
    CALL(FMI2SetInteger((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetBoolean(void* instance, const int vr[], int nvr, const int value[]) {
    CALL(FMI2SetBoolean((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetupExperiment(void* instance,
    int toleranceDefined,
    double tolerance,
    double startTime,
    int stopTimeDefined,
    double stopTime) {
    CALL(FMI2SetupExperiment((FMIInstance*)instance, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime));
}

void FMU_FMI2EnterInitializationMode(void* instance) {
    CALL(FMI2EnterInitializationMode((FMIInstance*)instance));
}

void FMU_FMI2ExitInitializationMode(void* instance) {
    CALL(FMI2ExitInitializationMode((FMIInstance*)instance));
}

/***************************************************
Model Exchange
****************************************************/

void FMU_FMI2EnterEventMode(void* instance) {
    CALL(FMI2EnterEventMode((FMIInstance*)instance));
}

void FMU_FMI2NewDiscreteStates(void* instance) {
    fmi2EventInfo eventInfo;
    do {
        CALL(FMI2NewDiscreteStates((FMIInstance*)instance, &eventInfo));
    } while (eventInfo.newDiscreteStatesNeeded);
}

void FMU_FMI2EnterContinuousTimeMode(void* instance) {
    CALL(FMI2EnterContinuousTimeMode((FMIInstance*)instance));
}

void FMU_FMI2SetTime(void* instance, double time) {
    CALL(FMI2SetTime((FMIInstance*)instance, time));
}

void FMU_FMI2SetContinuousStates(void* instance, const double x[], int nx) {
    CALL(FMI2SetContinuousStates((FMIInstance*)instance, x, nx));
}

void FMU_FMI2GetDerivatives(void* instance, double derivatives[], int nx) {
    CALL(FMI2GetDerivatives((FMIInstance*)instance, derivatives, nx));
}

void FMU_FMI2GetEventIndicators(void* instance, double eventIndicators[], int ni) {
    CALL(FMI2GetEventIndicators((FMIInstance*)instance, eventIndicators, ni));
}

void FMU_FMI2GetContinuousStates(void* instance, double x[], int nx) {
    CALL(FMI2GetContinuousStates((FMIInstance*)instance, x, nx));
}

/***************************************************
Co-Simulation
****************************************************/

void FMU_FMI2DoStep(void* externalObject,
    double currentCommunicationPoint,
    double communicationStepSize,
    int noSetFMUStatePriorToCurrentPoint) {

    FMIInstance* S = (FMIInstance*)externalObject;

    CALL(FMI2DoStep(S, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint));
}
