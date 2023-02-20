#pragma once

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

/***************************************************
Common Functions
****************************************************/

EXPORT void FMU_FMI2GetReal(void* instance, const int vr[], int nvr, double value[]);

EXPORT void FMU_FMI2GetInteger(void* instance, const int vr[], int nvr, int value[]);

EXPORT void FMU_FMI2GetBoolean(void* instance, const int vr[], int nvr, int value[]);

EXPORT void FMU_FMI2SetReal(void* instance, const int vr[], int nvr, const double value[]);

EXPORT void FMU_FMI2SetInteger(void* instance, const int vr[], int nvr, const int value[]);

EXPORT void FMU_FMI2SetBoolean(void* instance, const int vr[], int nvr, const int value[]);

EXPORT void FMU_FMI2SetString(void* instance, const int vr[], int nvr, const char* value[]);

EXPORT void FMU_FMI2SetupExperiment(void* instance,
    int toleranceDefined,
    double tolerance,
    double startTime,
    int stopTimeDefined,
    double stopTime);

EXPORT void FMU_FMI2EnterInitializationMode(void* instance);

EXPORT void FMU_FMI2ExitInitializationMode(void* instance);

/***************************************************
Model Exchange
****************************************************/

EXPORT void FMU_FMI2EnterEventMode(void* instance);

EXPORT void FMU_FMI2NewDiscreteStates(void* instance, int* valuesOfContinuousStatesChanged, double* nextEventTime);

EXPORT void FMU_FMI2EnterContinuousTimeMode(void* instance);

EXPORT void FMU_FMI2SetTime(void* instance, double time);

EXPORT void FMU_FMI2SetContinuousStates(void* instance, const double x[], int nx);

EXPORT void FMU_FMI2GetDerivatives(void* instance, double derivatives[], int nx);

EXPORT void FMU_FMI2GetEventIndicators(void* instance, double eventIndicators[], int ni);

EXPORT void FMU_FMI2GetContinuousStates(void* instance, double x[], int nx);

/***************************************************
Co-Simulation
****************************************************/

EXPORT void FMU_FMI2DoStep(void* externalObject,
    double currentCommunicationPoint,
    double communicationStepSize,
    int noSetFMUStatePriorToCurrentPoint);
