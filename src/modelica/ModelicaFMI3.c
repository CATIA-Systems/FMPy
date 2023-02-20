#include <math.h>

#include "ModelicaUtilities.h"
#include "ModelicaFMI3.h"
#include "FMI3.h"


#define CALL(f) do { if (f > FMIWarning) { ModelicaFormatError("The FMU reported an error."); } } while (0)

/***************************************************
Common Functions
****************************************************/

void FMU_FMI3EnterInitializationMode(
    void* instance,
    int toleranceDefined,
    double tolerance,
    double startTime,
    int stopTimeDefined,
    double stopTime) {

    CALL(FMI3EnterInitializationMode(
        (FMIInstance*)instance,
        toleranceDefined,
        tolerance,
        startTime,
        stopTimeDefined,
        stopTime
    ));
}

void FMU_FMI3ExitInitializationMode(void* instance) {
    CALL(FMI3ExitInitializationMode((FMIInstance*)instance));
}

void FMU_FMI3EnterEventMode(void* instance) {
    CALL(FMI3EnterEventMode((FMIInstance*)instance));
}

void FMU_FMI3GetFloat64(void* instance, const int valueReferences[], int nValueReferences, double values[]) {
    if (nValueReferences > 0) CALL(FMI3GetFloat64((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
}

void FMU_FMI3GetInt32(void* instance, const int valueReferences[], int nValueReferences, int values[]) {
    if (nValueReferences > 0) CALL(FMI3GetInt32((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
}

void FMU_FMI3GetBoolean(void* instance, const int valueReferences[], int nValueReferences, int values[]) {
    if (nValueReferences > 0) CALL(FMI3GetBoolean((FMIInstance*)instance, valueReferences, nValueReferences, (fmi3Boolean*)values, nValueReferences));
}

void FMU_FMI3SetFloat64(void* instance, const int valueReferences[], int nValueReferences, const double values[]) {
    if (nValueReferences > 0) CALL(FMI3SetFloat64((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
}

void FMU_FMI3SetInt32(void* instance, const int valueReferences[], int nValueReferences, const int values[]) {
    if (nValueReferences > 0) CALL(FMI3SetInt32((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
}

void FMU_FMI3SetBoolean(void* instance, const int valueReferences[], int nValueReferences, const int values[]) {
    if (nValueReferences > 0) CALL(FMI3SetBoolean((FMIInstance*)instance, valueReferences, nValueReferences, (fmi3Boolean*)values, nValueReferences));
}

void FMU_FMI3SetString(void* instance, const int valueReferences[], int nValueReferences, const char* values[]) {
    if (nValueReferences > 0) CALL(FMI3SetString((FMIInstance*)instance, valueReferences, nValueReferences, (fmi3String*)values, nValueReferences));
}

void FMU_FMI3UpdateDiscreteStates(void* instance, int* valuesOfContinuousStatesChanged, double* nextEventTime) {

    fmi3Boolean _discreteStatesNeedUpdate;
    fmi3Boolean _terminateSimulation;
    fmi3Boolean _nominalsOfContinuousStatesChanged;
    fmi3Boolean _valuesOfContinuousStatesChanged;
    fmi3Boolean _nextEventTimeDefined;
    fmi3Float64 _nextEventTime;

    do {
        CALL(FMI3UpdateDiscreteStates(
            (FMIInstance*)instance,
            &_discreteStatesNeedUpdate,
            &_terminateSimulation,
            &_nominalsOfContinuousStatesChanged,
            &_valuesOfContinuousStatesChanged,
            &_nextEventTimeDefined,
            &_nextEventTime
        ));
    } while (_discreteStatesNeedUpdate);

    *valuesOfContinuousStatesChanged = _valuesOfContinuousStatesChanged;
    *nextEventTime = _nextEventTimeDefined ? _nextEventTime : INFINITY;
}

/***************************************************
Functions for Model Exchange
****************************************************/

void FMU_FMI3EnterContinuousTimeMode(void* instance) {
    CALL(FMI3EnterContinuousTimeMode((FMIInstance*)instance));
}

void FMU_FMI3SetTime(void* instance, double time) {
    CALL(FMI3SetTime((FMIInstance*)instance, time));
}

void FMU_FMI3SetContinuousStates(void* instance, const double continuousStates[], int nContinuousStates) {
    if (nContinuousStates > 0) CALL(FMI3SetContinuousStates((FMIInstance*)instance, continuousStates, nContinuousStates));
}

void FMU_FMI3GetContinuousStateDerivatives(void* instance, double derivatives[], int nContinuousStates) {
    if (nContinuousStates > 0) CALL(FMI3GetContinuousStateDerivatives((FMIInstance*)instance, derivatives, nContinuousStates));
}

void FMU_FMI3GetEventIndicators(void* instance, double eventIndicators[], int nEventIndicators) {
    if (nEventIndicators > 0) CALL(FMI3GetEventIndicators((FMIInstance*)instance, eventIndicators, nEventIndicators));
}

void FMU_FMI3GetContinuousStates(void* instance, double continuousStates[], int nContinuousStates) {
    if (nContinuousStates > 0) CALL(FMI3GetContinuousStates((FMIInstance*)instance, continuousStates, nContinuousStates));
}

/***************************************************
Functions for Co-Simulation
****************************************************/

void FMU_FMI3DoStep(
    void* instance,
    double currentCommunicationPoint,
    double communicationStepSize) {

    fmi3Boolean eventHandlingNeeded;
    fmi3Boolean terminateSimulation;
    fmi3Boolean earlyReturn;
    fmi3Float64 lastSuccessfulTime;

    CALL(FMI3DoStep(
        (FMIInstance*)instance,
        currentCommunicationPoint,
        communicationStepSize,
        fmi3True,
        &eventHandlingNeeded,
        &terminateSimulation,
        &earlyReturn,
        &lastSuccessfulTime
    ));
}
