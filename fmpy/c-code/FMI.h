#ifndef FMI_H
#define FMI_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#ifdef _WIN32
#include <Windows.h>
#endif

#include <stdbool.h>

#ifndef FMI_MAX_MESSAGE_LENGTH
#define FMI_MAX_MESSAGE_LENGTH 4096
#endif

#ifndef FMI_STATIC
#define FMI_STATIC
#endif

typedef enum {
    FMIOK,
    FMIWarning,
    FMIDiscard,
    FMIError,
    FMIFatal,
    FMIPending
} FMIStatus;

typedef enum {

    // FMI 3.0 variable types
    FMIFloat32Type,
    FMIDiscreteFloat32Type,
    FMIFloat64Type,
    FMIDiscreteFloat64Type,
    FMIInt8Type,
    FMIUInt8Type,
    FMIInt16Type,
    FMIUInt16Type,
    FMIInt32Type,
    FMIUInt32Type,
    FMIInt64Type,
    FMIUInt64Type,
    FMIBooleanType,
    FMIStringType,
    FMIBinaryType,
    FMIClockType,

    // Aliases for FMI 1.0 and 2.0
    FMIRealType = FMIFloat64Type,
    FMIDiscreteRealType = FMIDiscreteFloat64Type,
    FMIIntegerType = FMIInt32Type,

} FMIVariableType;

typedef enum {
    FMIVersion1,
    FMIVersion2,
    FMIVersion3
} FMIVersion;

typedef enum {
    FMIModelExchange,
    FMICoSimulation,
    FMIScheduledExecution
} FMIInterfaceType;

typedef enum {
    FMI2StartAndEndState        = 1 << 0,
    FMI2InstantiatedState       = 1 << 1,
    FMI2InitializationModeState = 1 << 2,

    // model exchange states
    FMI2EventModeState          = 1 << 3,
    FMI2ContinuousTimeModeState = 1 << 4,

    // co-simulation states
    FMI2StepCompleteState       = 1 << 5,
    FMI2StepInProgressState     = 1 << 6,
    FMI2StepFailedState         = 1 << 7,
    FMI2StepCanceledState       = 1 << 8,

    FMI2TerminatedState         = 1 << 9,
    FMI2ErrorState              = 1 << 10,
    FMI2FatalState              = 1 << 11,
} FMI2State;

typedef unsigned int FMIValueReference;

typedef struct FMIInstance_ FMIInstance;

typedef struct FMI1Functions_ FMI1Functions;

typedef struct FMI2Functions_ FMI2Functions;

typedef struct FMI3Functions_ FMI3Functions;

typedef void FMILogFunctionCall(FMIInstance *instance, FMIStatus status, const char *message, ...);

typedef void FMILogMessage(FMIInstance *instance, FMIStatus status, const char *category, const char *message);

struct FMIInstance_ {

    FMI1Functions *fmi1Functions;
    FMI2Functions *fmi2Functions;
    FMI3Functions *fmi3Functions;

#ifdef _WIN32
    HMODULE libraryHandle;
#else
    void *libraryHandle;
#endif

    void *userData;

    FMILogMessage      *logMessage;
    FMILogFunctionCall *logFunctionCall;

    double time;

    char *buf1;
    char *buf2;

    size_t bufsize1;
    size_t bufsize2;

    void *component;

    const char *name;

    bool logFMICalls;

    FMI2State state;

    FMIStatus status;

    FMIVersion fmiVersion;

    FMIInterfaceType interfaceType;

};

FMI_STATIC FMIInstance *FMICreateInstance(const char *instanceName, const char *libraryPath, FMILogMessage *logMessage, FMILogFunctionCall *logFunctionCall);

FMI_STATIC void FMIFreeInstance(FMIInstance *instance);

FMI_STATIC const char* FMIValueReferencesToString(FMIInstance *instance, const FMIValueReference vr[], size_t nvr);

FMI_STATIC const char* FMIValuesToString(FMIInstance *instance, size_t nvr, const void *value, FMIVariableType variableType);

FMI_STATIC FMIStatus FMIURIToPath(const char *uri, char *path, const size_t pathLength);

FMI_STATIC FMIStatus FMIPathToURI(const char *path, char *uri, const size_t uriLength);

FMI_STATIC FMIStatus FMIPlatformBinaryPath(const char *unzipdir, const char *modelIdentifier, FMIVersion fmiVersion, char *platformBinaryPath, size_t size);


#ifdef __cplusplus
}  /* end of extern "C" { */
#endif

#endif // FMI_H
