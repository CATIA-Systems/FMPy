#pragma once

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

/***************************************************
Common Functions
****************************************************/

EXPORT void FMU_FMI3EnterInitializationMode(
    void* instance,
    int toleranceDefined,
    double tolerance,
    double startTime,
    int stopTimeDefined,
    double stopTime);

EXPORT void FMU_FMI3ExitInitializationMode(void* instance);

EXPORT void FMU_FMI3GetFloat64(void* instance, const int valueReferences[], int nValueReferences, double values[]);

EXPORT void FMU_FMI3SetFloat64(void* instance, const int valueReferences[], int nValueReferences, const double values[]);

/***************************************************
Functions for Co-Simulation
****************************************************/

EXPORT void FMU_FMI3DoStep(
    void* instance,
    double currentCommunicationPoint,
    double communicationStepSize);
