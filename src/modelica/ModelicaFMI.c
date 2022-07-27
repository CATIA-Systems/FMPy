#include <stdio.h>
#include <math.h>

#include "ModelicaFMI.h"
#include "ModelicaUtilities.h"
#include "FMI2.h"
#include "FMI3.h"


static void logMessage(FMIInstance* instance, FMIStatus status, const char* category, const char* message) {
    ModelicaFormatMessage("%s\n", message);
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


void* FMU_load(ModelicaUtilityFunctions_t* callbacks, const char* unzipdir, int fmiVersion, const char* modelIdentifier, const char* instanceName, int interfaceType, const char* instantiationToken, int visible, int loggingOn, int logFMICalls) {

    setModelicaUtilityFunctions(callbacks);

    char platformBinaryPath[2048] = "";

    FMIPlatformBinaryPath(unzipdir, modelIdentifier, fmiVersion, platformBinaryPath, 2048);

    FMIInstance* S = FMICreateInstance(instanceName, platformBinaryPath, logMessage, logFMICalls ? logFunctionCall : NULL);

    if (!S) {
        ModelicaFormatError("Failed to load platform binary %s.", platformBinaryPath);
    }

    char resourceURI[2048] = "";

    FMIPathToURI(unzipdir, resourceURI, 2048);

    FMIStatus status = FMIFatal;

    switch (fmiVersion) {
    case FMIVersion2:
        status = FMI2Instantiate(S, resourceURI, (fmi2Type)interfaceType, instantiationToken, visible, loggingOn);
        break;
    case FMIVersion3:
        status = interfaceType == FMIModelExchange ?
            FMI3InstantiateModelExchange(
                S,                  // instance,
                instantiationToken, // instantiationToken,
                "",                 // resourcePath,
                visible,            // visible,
                loggingOn           // loggingOn
            ) :
            FMI3InstantiateCoSimulation(
                S,            // instance,
                instantiationToken, // instantiationToken,
                "",           // resourcePath,
                visible,      // visible,
                loggingOn,    // loggingOn,
                fmi3False,    // eventModeUsed,
                fmi3False,    // earlyReturnAllowed,
                NULL,         // requiredIntermediateVariables[],
                0,            // nRequiredIntermediateVariables,
                NULL          // intermediateUpdate
            );
        break;
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
