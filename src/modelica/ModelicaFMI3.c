#include <math.h>

#include "ModelicaFMI3.h"
#include "ModelicaUtilities.h"
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

void FMU_FMI3GetFloat64(void* instance, const int valueReferences[], int nValueReferences, double values[]) {
    CALL(FMI3GetFloat64((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
}

void FMU_FMI3SetFloat64(void* instance, const int valueReferences[], int nValueReferences, const double values[]) {
    CALL(FMI3SetFloat64((FMIInstance*)instance, valueReferences, nValueReferences, values, nValueReferences));
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
