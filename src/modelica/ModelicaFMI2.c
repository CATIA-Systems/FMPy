#include <math.h>

#include "ModelicaUtilities.h"
#include "ModelicaFMI2.h"
#include "FMI2.h"


#define CALL(f) do { if (f > FMIWarning) { ModelicaFormatError("The FMU reported an error."); } } while (0)


/***************************************************
Common Functions
****************************************************/

void FMU_FMI2GetReal(void* instance, const int vr[], int nvr, double value[]) {
    if (nvr > 0) CALL(FMI2GetReal((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2GetInteger(void* instance, const int vr[], int nvr, int value[]) {
    if (nvr > 0) CALL(FMI2GetInteger((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2GetBoolean(void* instance, const int vr[], int nvr, int value[]) {
    if (nvr > 0) CALL(FMI2GetBoolean((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetReal(void* instance, const int vr[], int nvr, const double value[]) {
    if (nvr > 0) CALL(FMI2SetReal((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetInteger(void* instance, const int vr[], int nvr, const int value[]) {
    if (nvr > 0) CALL(FMI2SetInteger((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetBoolean(void* instance, const int vr[], int nvr, const int value[]) {
    if (nvr > 0) CALL(FMI2SetBoolean((FMIInstance*)instance, vr, nvr, value));
}

void FMU_FMI2SetString(void* instance, const int vr[], int nvr, const char* value[]) {
    if (nvr > 0) CALL(FMI2SetString((FMIInstance*)instance, vr, nvr, value));
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

void FMU_FMI2NewDiscreteStates(void* instance, int* valuesOfContinuousStatesChanged, double* nextEventTime) {

    fmi2EventInfo eventInfo;

    do {
        CALL(FMI2NewDiscreteStates((FMIInstance*)instance, &eventInfo));
    } while (eventInfo.newDiscreteStatesNeeded);

    *nextEventTime = eventInfo.nextEventTimeDefined ? eventInfo.nextEventTime : INFINITY;
    *valuesOfContinuousStatesChanged = eventInfo.valuesOfContinuousStatesChanged;
}

void FMU_FMI2EnterContinuousTimeMode(void* instance) {
    CALL(FMI2EnterContinuousTimeMode((FMIInstance*)instance));
}

void FMU_FMI2SetTime(void* instance, double time) {
    CALL(FMI2SetTime((FMIInstance*)instance, time));
}

void FMU_FMI2SetContinuousStates(void* instance, const double x[], int nx) {
    if (nx > 0) CALL(FMI2SetContinuousStates((FMIInstance*)instance, x, nx));
}

void FMU_FMI2GetDerivatives(void* instance, double derivatives[], int nx) {
    if (nx > 0) CALL(FMI2GetDerivatives((FMIInstance*)instance, derivatives, nx));
}

void FMU_FMI2GetEventIndicators(void* instance, double eventIndicators[], int ni) {
    if (ni > 0) CALL(FMI2GetEventIndicators((FMIInstance*)instance, eventIndicators, ni));
}

void FMU_FMI2GetContinuousStates(void* instance, double x[], int nx) {
    if (nx > 0) CALL(FMI2GetContinuousStates((FMIInstance*)instance, x, nx));
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
