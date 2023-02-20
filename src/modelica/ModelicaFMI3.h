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

EXPORT void FMU_FMI3EnterEventMode(void* instance);

EXPORT void FMU_FMI3GetFloat64(void* instance, const int valueReferences[], int nValueReferences, double values[]);

EXPORT void FMU_FMI3GetInt32(void* instance, const int valueReferences[], int nValueReferences, int values[]);

EXPORT void FMU_FMI3GetBoolean(void* instance, const int valueReferences[], int nValueReferences, int values[]);

EXPORT void FMU_FMI3SetFloat64(void* instance, const int valueReferences[], int nValueReferences, const double values[]);

EXPORT void FMU_FMI3SetInt32(void* instance, const int valueReferences[], int nValueReferences, const int values[]);

EXPORT void FMU_FMI3SetBoolean(void* instance, const int valueReferences[], int nValueReferences, const int values[]);

EXPORT void FMU_FMI3SetString(void* instance, const int valueReferences[], int nValueReferences, const char* values[]);

EXPORT void FMU_FMI3UpdateDiscreteStates(void* instance, int* valuesOfContinuousStatesChanged, double* nextEventTime);

/***************************************************
Functions for Model Exchange
****************************************************/

EXPORT void FMU_FMI3EnterContinuousTimeMode(void* instance);

EXPORT void FMU_FMI3SetTime(void* instance, double time);

EXPORT void FMU_FMI3SetContinuousStates(void* instance, const double continuousStates[], int nContinuousStates);

EXPORT void FMU_FMI3GetContinuousStateDerivatives(void* instance, double derivatives[], int nContinuousStates);

EXPORT void FMU_FMI3GetEventIndicators(void* instance, double eventIndicators[], int nEventIndicators);

EXPORT void FMU_FMI3GetContinuousStates(void* instance, double continuousStates[], int nContinuousStates);

/***************************************************
Functions for Co-Simulation
****************************************************/

EXPORT void FMU_FMI3DoStep(void* instance, double currentCommunicationPoint, double communicationStepSize);
