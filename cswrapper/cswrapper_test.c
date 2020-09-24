#ifdef _WIN32
#include <Windows.h>
#else
#include <dlfcn.h>
#endif
#include <stdlib.h>
#include <stdio.h>

#include "fmi2Functions.h"

typedef struct {

#if defined(_WIN32)
    HMODULE libraryHandle;
#else
    void *libraryHandle;
#endif

    fmi2Component c;

    /***************************************************
    Common Functions
    ****************************************************/
    fmi2GetTypesPlatformTYPE         *fmi2GetTypesPlatform;
    fmi2GetVersionTYPE               *fmi2GetVersion;
    fmi2SetDebugLoggingTYPE          *fmi2SetDebugLogging;
    fmi2InstantiateTYPE              *fmi2Instantiate;
    fmi2FreeInstanceTYPE             *fmi2FreeInstance;
    fmi2SetupExperimentTYPE          *fmi2SetupExperiment;
    fmi2EnterInitializationModeTYPE  *fmi2EnterInitializationMode;
    fmi2ExitInitializationModeTYPE   *fmi2ExitInitializationMode;
    fmi2TerminateTYPE                *fmi2Terminate;
    fmi2ResetTYPE                    *fmi2Reset;
    fmi2GetRealTYPE                  *fmi2GetReal;
    fmi2GetIntegerTYPE               *fmi2GetInteger;
    fmi2GetBooleanTYPE               *fmi2GetBoolean;
    fmi2GetStringTYPE                *fmi2GetString;
    fmi2SetRealTYPE                  *fmi2SetReal;
    fmi2SetIntegerTYPE               *fmi2SetInteger;
    fmi2SetBooleanTYPE               *fmi2SetBoolean;
    fmi2SetStringTYPE                *fmi2SetString;
    fmi2GetFMUstateTYPE              *fmi2GetFMUstate;
    fmi2SetFMUstateTYPE              *fmi2SetFMUstate;
    fmi2FreeFMUstateTYPE             *fmi2FreeFMUstate;
    fmi2SerializedFMUstateSizeTYPE   *fmi2SerializedFMUstateSize;
    fmi2SerializeFMUstateTYPE        *fmi2SerializeFMUstate;
    fmi2DeSerializeFMUstateTYPE      *fmi2DeSerializeFMUstate;
    fmi2GetDirectionalDerivativeTYPE *fmi2GetDirectionalDerivative;


    /***************************************************
    Functions for FMI2 for Model Exchange
    ****************************************************/
    fmi2EnterEventModeTYPE                *fmi2EnterEventMode;
    fmi2NewDiscreteStatesTYPE             *fmi2NewDiscreteStates;
    fmi2EnterContinuousTimeModeTYPE       *fmi2EnterContinuousTimeMode;
    fmi2CompletedIntegratorStepTYPE       *fmi2CompletedIntegratorStep;
    fmi2SetTimeTYPE                       *fmi2SetTime;
    fmi2SetContinuousStatesTYPE           *fmi2SetContinuousStates;
    fmi2GetDerivativesTYPE                *fmi2GetDerivatives;
    fmi2GetEventIndicatorsTYPE            *fmi2GetEventIndicators;
    fmi2GetContinuousStatesTYPE           *fmi2GetContinuousStates;
    fmi2GetNominalsOfContinuousStatesTYPE *fmi2GetNominalsOfContinuousStates;

} Model;

/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
const char* fmi2GetTypesPlatform(void) { return fmi2TypesPlatform; }

const char* fmi2GetVersion(void) { return fmi2Version; }

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {
    if (!c) return fmi2Error;
    Model *m = (Model *)c;
    return m->fmi2SetDebugLogging(c, loggingOn, nCategories, categories);
}

#define GET(f) m->f = dlsym(m->libraryHandle, #f);

/* Creation and destruction of FMU instances and setting debug status */
fmi2Component fmi2Instantiate(fmi2String instanceName,
                              fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions* functions,
                              fmi2Boolean visible,
                              fmi2Boolean loggingOn) {

    if (fmuType != fmi2CoSimulation) {
        if (functions && functions->logger) {
            functions->logger(NULL, instanceName, fmi2Error, "logError", "Argument fmuType must be fmi2CoSimulation.");
        }
        return NULL;
    }

    Model *m = calloc(1, sizeof(Model));

    const char *dll = "/Users/tors10/Development/Reference-FMUs/build/temp/VanDerPol/binaries/darwin64/VanDerPol.dylib";

    m->libraryHandle = dlopen(dll, RTLD_LAZY);

    GET(fmi2GetTypesPlatform)
    GET(fmi2GetVersion)
    GET(fmi2SetDebugLogging)
    GET(fmi2Instantiate)
    GET(fmi2FreeInstance)
    GET(fmi2SetupExperiment)
    GET(fmi2EnterInitializationMode)
    GET(fmi2ExitInitializationMode)
    GET(fmi2Terminate)
    GET(fmi2Reset)
    GET(fmi2GetReal)
    GET(fmi2GetInteger)
    GET(fmi2GetBoolean)
    GET(fmi2GetString)
    GET(fmi2SetReal)
    GET(fmi2SetInteger)
    GET(fmi2SetBoolean)
    GET(fmi2SetString)
    GET(fmi2GetFMUstate)
    GET(fmi2SetFMUstate)
    GET(fmi2FreeFMUstate)
    GET(fmi2SerializedFMUstateSize)
    GET(fmi2SerializeFMUstate)
    GET(fmi2DeSerializeFMUstate)
    GET(fmi2GetDirectionalDerivative)

    GET(fmi2EnterEventMode)
    GET(fmi2NewDiscreteStates)
    GET(fmi2EnterContinuousTimeMode)
    GET(fmi2CompletedIntegratorStep)
    GET(fmi2SetTime)
    GET(fmi2SetContinuousStates)
    GET(fmi2GetDerivatives)
    GET(fmi2GetEventIndicators)
    GET(fmi2GetContinuousStates)
    GET(fmi2GetNominalsOfContinuousStates)

    m->c = m->fmi2Instantiate(instanceName, fmuType, fmuGUID, fmuResourceLocation, functions, visible, loggingOn);

    return m;

}

void fmi2FreeInstance(fmi2Component c) {
    if (!c) return;
    Model *m = (Model *)c;
    dlclose(m->libraryHandle);
    free(m);
}


/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
                                       const fmi2ValueReference vr[], size_t nvr,
                                       const fmi2Integer order[],
                                       const fmi2Real value[]) {
    return fmi2Error;
}
fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
                                        const fmi2ValueReference vr[], size_t nvr,
                                        const fmi2Integer order[],
                                        fmi2Real value[]) {
    return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c,
                      fmi2Real      currentCommunicationPoint,
                      fmi2Real      communicationStepSize,
                      fmi2Boolean   noSetFMUStatePriorToCurrentPoint) {
    return fmi2Error;
}

fmi2Status fmi2CancelStep(fmi2Component c) {
    return fmi2Error;
}

/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status*  value) {
    return fmi2Error;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real*    value) {
    return fmi2Error;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
    return fmi2Error;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
    return fmi2Error;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String*  value) {
    return fmi2Error;
}

static void cb_logMessage(fmi2ComponentEnvironment componentEnvironment,
                            fmi2String instanceName,
                            fmi2Status status,
                            fmi2String category,
                            fmi2String message,
                            ...) {

    puts(message);
}

int main(int argc, char *argv[]) {
    
//    const char *dll = "/Users/tors10/Development/Reference-FMUs/build/temp/VanDerPol/binaries/darwin64/VanDerPol.dylib";

    void *libraryHandle = dlopen("cswrapper.dylib", RTLD_LAZY);
    
    fmi2InstantiateTYPE *instantiate = dlsym(libraryHandle, "fmi2Instantiate");
    
    fmi2CallbackFunctions functions = { .logger = cb_logMessage };
    
    fmi2Component c = instantiate("instance1", fmi2CoSimulation, "{8c4e810f-3da3-4a00-8276-176fa3c9f000}", "", &functions, fmi2False, fmi2False);

    dlclose(libraryHandle);

//    fmi2CallbackFunctions functions = { .logger = cb_logMessage };
//
//    fmi2Component c = fmi2Instantiate("instance1", fmi2CoSimulation, "{8c4e810f-3da3-4a00-8276-176fa3c9f000}", "", &functions, fmi2False, fmi2False);
//
//    fmi2FreeInstance(c);

    return 0;
}
