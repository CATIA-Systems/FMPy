#ifndef FMI2_H
#define FMI2_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#include "FMI.h"


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

#endif // FMI2_H
