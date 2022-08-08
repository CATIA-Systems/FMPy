#include <stdio.h>
#include <string.h>
#include <math.h>

#include "ModelicaFMI.h"
#include "ModelicaUtilities.h"
#include "FMI2.h"
#include "FMI3.h"


static void logMessage(FMIInstance* instance, FMIStatus status, const char* category, const char* message) {
    ModelicaFormatMessage("%s\n", message);
}

static void logFunctionCall(FMIInstance* instance, FMIStatus status, const char* message, ...) {

    va_list args;
    va_start(args, message);

    const char* suffix;

    switch (status) {
    case FMIOK:
        suffix = " -> OK\n";
        break;
    case FMIWarning:
        suffix = " -> Warning\n";
        break;
    case FMIDiscard:
        suffix = " -> Discard\n";
        break;
    case FMIError:
        suffix = " -> Error\n";
        break;
    case FMIFatal:
        suffix = " -> Fatal\n";
        break;
    case FMIPending:
        suffix = " -> Pending\n";
        break;
    default:
        suffix = " -> Illegal return code\n";
        break;
    }

    FILE* logFile = (FILE*)instance->userData;

    if (logFile) {
        vfprintf(logFile, message, args);
        fprintf(logFile, suffix);
    } else {
        ModelicaVFormatMessage(message, args);
        ModelicaFormatMessage(suffix);
    }
    
    va_end(args);
}


void* FMU_load(
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
    const char* logFile) {

    setModelicaUtilityFunctions(callbacks);

    char platformBinaryPath[2048] = "";

    FMIPlatformBinaryPath(unzipdir, modelIdentifier, fmiVersion, platformBinaryPath, 2048);

    FMIInstance* S = FMICreateInstance(instanceName, platformBinaryPath, logMessage, logFMICalls ? logFunctionCall : NULL);

    if (logToFile && logFile) {
        S->userData = fopen(logFile, "w");
    }

    if (!S) {
        ModelicaFormatError("Failed to load platform binary %s.", platformBinaryPath);
    }

    char resourcePath[4096] = "";

    strcpy(resourcePath, unzipdir);

#ifdef _WIN32
    strcat(resourcePath, "\\resources\\");
    _fullpath(resourcePath, resourcePath, sizeof(resourcePath));
#else
    strcat(resourcePath, "/resources/");
    realpath(resourcePath, resourcePath);
#endif

    FMIStatus status = FMIFatal;

    if (fmiVersion == FMIVersion2) {
        char resourceURI[4096] = "";
        FMIPathToURI(resourcePath, resourceURI, 4096);
        status = FMI2Instantiate(S, resourceURI, (fmi2Type)interfaceType, instantiationToken, visible, loggingOn);
    } else {
        status = interfaceType == FMIModelExchange ?
            FMI3InstantiateModelExchange(
                S,                  // instance,
                instantiationToken, // instantiationToken,
                resourcePath,       // resourcePath,
                visible,            // visible,
                loggingOn           // loggingOn
            ) :
            FMI3InstantiateCoSimulation(
                S,                  // instance,
                instantiationToken, // instantiationToken,
                resourcePath,       // resourcePath,
                visible,            // visible,
                loggingOn,          // loggingOn,
                fmi3False,          // eventModeUsed,
                fmi3False,          // earlyReturnAllowed,
                NULL,               // requiredIntermediateVariables[],
                0,                  // nRequiredIntermediateVariables,
                NULL                // intermediateUpdate
            );
    }

    if (status > FMIOK) {
        ModelicaFormatError("Failed to instantiate FMU %s.", platformBinaryPath);
    }
	
	return S;
}

void FMU_free(void* instance) {

    // TODO: terminate

    FMIInstance* S = (FMIInstance*)instance;
    FMIFreeInstance(S);
}
