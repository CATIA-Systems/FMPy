#pragma once

#include "ModelicaUtilityFunctions.h"

#ifdef _MSC_VER
#define EXPORT __declspec(dllexport)
#else
#define EXPORT __attribute__((visibility("default")))
#endif

EXPORT void* FMU_load(
    ModelicaUtilityFunctions_t* callbacks,
    const char* unzipdir,
    int fmiVersion,
    const char* modelIdentifier,
    const char* instanceName,
    int interfaceType,
    const char* instantiationToken,
    int visible,
    int loggingOn,
    int logFMICalls,
    int logToFile,
    const char* logFile);

EXPORT void FMU_free(void* instance);
