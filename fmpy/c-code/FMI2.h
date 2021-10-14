#ifndef FMI2_H
#define FMI2_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#include "fmi2Functions.h"
#include "FMI.h"

struct FMI2Functions_ {

    fmi2CallbackFunctions            callbacks;
    fmi2EventInfo                    eventInfo;

    /***************************************************
    Common Functions for FMI 2.0
    ****************************************************/

    /* required functions */
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

    /* optional functions */
    fmi2GetFMUstateTYPE              *fmi2GetFMUstate;
    fmi2SetFMUstateTYPE              *fmi2SetFMUstate;
    fmi2FreeFMUstateTYPE             *fmi2FreeFMUstate;
    fmi2SerializedFMUstateSizeTYPE   *fmi2SerializedFMUstateSize;
    fmi2SerializeFMUstateTYPE        *fmi2SerializeFMUstate;
    fmi2DeSerializeFMUstateTYPE      *fmi2DeSerializeFMUstate;
    fmi2GetDirectionalDerivativeTYPE *fmi2GetDirectionalDerivative;

    /***************************************************
    Functions for FMI 2.0 for Model Exchange
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

    /***************************************************
    Functions for FMI 2.0 for Co-Simulation
    ****************************************************/

    fmi2SetRealInputDerivativesTYPE  *fmi2SetRealInputDerivatives;
    fmi2GetRealOutputDerivativesTYPE *fmi2GetRealOutputDerivatives;
    fmi2DoStepTYPE                   *fmi2DoStep;
    fmi2CancelStepTYPE               *fmi2CancelStep;
    fmi2GetStatusTYPE                *fmi2GetStatus;
    fmi2GetRealStatusTYPE            *fmi2GetRealStatus;
    fmi2GetIntegerStatusTYPE         *fmi2GetIntegerStatus;
    fmi2GetBooleanStatusTYPE         *fmi2GetBooleanStatus;
    fmi2GetStringStatusTYPE          *fmi2GetStringStatus;

};


/***************************************************
Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
FMI_STATIC const char* FMI2GetTypesPlatform(FMIInstance *instance);

FMI_STATIC const char* FMI2GetVersion(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2SetDebugLogging(FMIInstance *instance, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]);

FMI_STATIC fmi2Status FMI2Instantiate(FMIInstance *instance, const char *fmuResourceLocation, fmi2Type fmuType, fmi2String fmuGUID,
    fmi2Boolean visible, fmi2Boolean loggingOn);

FMI_STATIC void FMI2FreeInstance(FMIInstance *instance);

/* Enter and exit initialization mode, terminate and reset */
FMI_STATIC fmi2Status FMI2SetupExperiment(FMIInstance *instance,
    fmi2Boolean toleranceDefined,
    fmi2Real tolerance,
    fmi2Real startTime,
    fmi2Boolean stopTimeDefined,
    fmi2Real stopTime);

FMI_STATIC fmi2Status FMI2EnterInitializationMode(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2ExitInitializationMode(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2Terminate(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2Reset(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2SetupExperiment(FMIInstance *instance,
    fmi2Boolean toleranceDefined,
    fmi2Real tolerance,
    fmi2Real startTime,
    fmi2Boolean stopTimeDefined,
    fmi2Real stopTime);

/* Getting and setting variable values */
FMI_STATIC fmi2Status FMI2GetReal(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]);

FMI_STATIC fmi2Status FMI2GetInteger(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]);

FMI_STATIC fmi2Status FMI2GetBoolean(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]);

FMI_STATIC fmi2Status FMI2GetString(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]);

FMI_STATIC fmi2Status FMI2SetReal(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Real    value[]);

FMI_STATIC fmi2Status FMI2SetInteger(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]);

FMI_STATIC fmi2Status FMI2SetBoolean(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]);

FMI_STATIC fmi2Status FMI2SetString(FMIInstance *instance, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]);

/* Getting and setting the internal FMU state */
FMI_STATIC fmi2Status FMI2GetFMUstate(FMIInstance *instance, fmi2FMUstate* FMUstate);

FMI_STATIC fmi2Status FMI2SetFMUstate(FMIInstance *instance, fmi2FMUstate  FMUstate);

FMI_STATIC fmi2Status FMI2FreeFMUstate(FMIInstance *instance, fmi2FMUstate* FMUstate);

FMI_STATIC fmi2Status FMI2SerializedFMUstateSize(FMIInstance *instance, fmi2FMUstate  FMUstate, size_t* size);

FMI_STATIC fmi2Status FMI2SerializeFMUstate(FMIInstance *instance, fmi2FMUstate  FMUstate, fmi2Byte serializedState[], size_t size);

FMI_STATIC fmi2Status FMI2DeSerializeFMUstate(FMIInstance *instance, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate);

/* Getting partial derivatives */
FMI_STATIC fmi2Status FMI2GetDirectionalDerivative(FMIInstance *instance,
    const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
    const fmi2ValueReference vKnown_ref[], size_t nKnown,
    const fmi2Real dvKnown[],
    fmi2Real dvUnknown[]);

/***************************************************
Types for Functions for FMI2 for Model Exchange
****************************************************/

/* Enter and exit the different modes */
FMI_STATIC fmi2Status FMI2EnterEventMode(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2NewDiscreteStates(FMIInstance *instance, fmi2EventInfo *eventInfo);

FMI_STATIC fmi2Status FMI2EnterContinuousTimeMode(FMIInstance *instance);

FMI_STATIC fmi2Status FMI2CompletedIntegratorStep(FMIInstance *instance,
    fmi2Boolean   noSetFMUStatePriorToCurrentPoint,
    fmi2Boolean*  enterEventMode,
    fmi2Boolean*  terminateSimulation);

/* Providing independent variables and re-initialization of caching */
FMI_STATIC fmi2Status FMI2SetTime(FMIInstance *instance, fmi2Real time);

FMI_STATIC fmi2Status FMI2SetContinuousStates(FMIInstance *instance, const fmi2Real x[], size_t nx);

/* Evaluation of the model equations */
FMI_STATIC fmi2Status FMI2GetDerivatives(FMIInstance *instance, fmi2Real derivatives[], size_t nx);

FMI_STATIC fmi2Status FMI2GetEventIndicators(FMIInstance *instance, fmi2Real eventIndicators[], size_t ni);

FMI_STATIC fmi2Status FMI2GetContinuousStates(FMIInstance *instance, fmi2Real x[], size_t nx);

FMI_STATIC fmi2Status FMI2GetNominalsOfContinuousStates(FMIInstance *instance, fmi2Real x_nominal[], size_t nx);


/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
FMI_STATIC fmi2Status FMI2SetRealInputDerivatives(FMIInstance *instance,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    const fmi2Real value[]);

FMI_STATIC fmi2Status FMI2GetRealOutputDerivatives(FMIInstance *instance,
    const fmi2ValueReference vr[], size_t nvr,
    const fmi2Integer order[],
    fmi2Real value[]);

FMI_STATIC fmi2Status FMI2DoStep(FMIInstance *instance,
    fmi2Real      currentCommunicationPoint,
    fmi2Real      communicationStepSize,
    fmi2Boolean   noSetFMUStatePriorToCurrentPoint);

FMI_STATIC fmi2Status FMI2CancelStep(FMIInstance *instance);

/* Inquire slave status */
FMI_STATIC fmi2Status FMI2GetStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Status* value);

FMI_STATIC fmi2Status FMI2GetRealStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Real* value);

FMI_STATIC fmi2Status FMI2GetIntegerStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Integer* value);

FMI_STATIC fmi2Status FMI2GetBooleanStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2Boolean* value);

FMI_STATIC fmi2Status FMI2GetStringStatus(FMIInstance *instance, const fmi2StatusKind s, fmi2String*  value);

#ifdef __cplusplus
}  /* end of extern "C" { */
#endif

#endif // FMI2_H
