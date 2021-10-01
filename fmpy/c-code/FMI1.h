#ifndef FMI1_H
#define FMI1_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#include "FMI.h"


/***************************************************
 Common Functions for FMI 1.0
****************************************************/
FMI_STATIC fmi1Status    FMI1SetReal         (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Real    value[]);
FMI_STATIC fmi1Status    FMI1SetInteger      (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer value[]);
FMI_STATIC fmi1Status    FMI1SetBoolean      (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Boolean value[]);
FMI_STATIC fmi1Status    FMI1SetString       (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1String  value[]);
FMI_STATIC fmi1Status    FMI1GetReal         (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr,       fmi1Real    value[]);
FMI_STATIC fmi1Status    FMI1GetInteger      (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr,       fmi1Integer value[]);
FMI_STATIC fmi1Status    FMI1GetBoolean      (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr,       fmi1Boolean value[]);
FMI_STATIC fmi1Status    FMI1GetString       (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr,       fmi1String  value[]);
FMI_STATIC fmi1Status    FMI1SetDebugLogging (FMIInstance *instance, fmi1Boolean loggingOn);

/***************************************************
 FMI 1.0 for Model Exchange Functions
****************************************************/
FMI_STATIC const char*   FMI1GetModelTypesPlatform      (FMIInstance *instance);
FMI_STATIC const char*   FMI1GetVersion                 (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1InstantiateModel           (FMIInstance *instance, fmi1String modelIdentifier, fmi1String GUID, fmi1Boolean loggingOn);
FMI_STATIC void          FMI1FreeModelInstance          (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1SetTime                    (FMIInstance *instance, fmi1Real time);
FMI_STATIC fmi1Status    FMI1SetContinuousStates        (FMIInstance *instance, const fmi1Real x[], size_t nx);
FMI_STATIC fmi1Status    FMI1CompletedIntegratorStep    (FMIInstance *instance, fmi1Boolean* callEventUpdate);
FMI_STATIC fmi1Status    FMI1Initialize                 (FMIInstance *instance, fmi1Boolean toleranceControlled, fmi1Real relativeTolerance);
FMI_STATIC fmi1Status    FMI1GetDerivatives             (FMIInstance *instance, fmi1Real derivatives[], size_t nx);
FMI_STATIC fmi1Status    FMI1GetEventIndicators         (FMIInstance *instance, fmi1Real eventIndicators[], size_t ni);
FMI_STATIC fmi1Status    FMI1EventUpdate                (FMIInstance *instance, fmi1Boolean intermediateResults, fmi1EventInfo* eventInfo);
FMI_STATIC fmi1Status    FMI1GetContinuousStates        (FMIInstance *instance, fmi1Real states[], size_t nx);
FMI_STATIC fmi1Status    FMI1GetNominalContinuousStates (FMIInstance *instance, fmi1Real x_nominal[], size_t nx);
FMI_STATIC fmi1Status    FMI1GetStateValueReferences    (FMIInstance *instance, fmi1ValueReference vrx[], size_t nx);
FMI_STATIC fmi1Status    FMI1Terminate                  (FMIInstance *instance);

/***************************************************
 FMI 1.0 for Co-Simulation Functions
****************************************************/
FMI_STATIC const char*   FMI1GetTypesPlatform         (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1InstantiateSlave         (FMIInstance *instance, fmi1String modelIdentifier, fmi1String fmuGUID, fmi1String fmuLocation, fmi1String  mimeType, fmi1Real timeout, fmi1Boolean visible, fmi1Boolean interactive, fmi1Boolean loggingOn);
FMI_STATIC fmi1Status    FMI1InitializeSlave          (FMIInstance *instance, fmi1Real tStart, fmi1Boolean StopTimeDefined, fmi1Real tStop);
FMI_STATIC fmi1Status    FMI1TerminateSlave           (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1ResetSlave               (FMIInstance *instance);
FMI_STATIC void          FMI1FreeSlaveInstance        (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1SetRealInputDerivatives  (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer order[], const fmi1Real value[]);
FMI_STATIC fmi1Status    FMI1GetRealOutputDerivatives (FMIInstance *instance, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer order[],       fmi1Real value[]);
FMI_STATIC fmi1Status    FMI1CancelStep               (FMIInstance *instance);
FMI_STATIC fmi1Status    FMI1DoStep                   (FMIInstance *instance, fmi1Real currentCommunicationPoint, fmi1Real communicationStepSize, fmi1Boolean newStep);
FMI_STATIC fmi1Status    FMI1GetStatus                (FMIInstance *instance, const fmi1StatusKind s, fmi1Status*  value);
FMI_STATIC fmi1Status    FMI1GetRealStatus            (FMIInstance *instance, const fmi1StatusKind s, fmi1Real*    value);
FMI_STATIC fmi1Status    FMI1GetIntegerStatus         (FMIInstance *instance, const fmi1StatusKind s, fmi1Integer* value);
FMI_STATIC fmi1Status    FMI1GetBooleanStatus         (FMIInstance *instance, const fmi1StatusKind s, fmi1Boolean* value);
FMI_STATIC fmi1Status    FMI1GetStringStatus          (FMIInstance *instance, const fmi1StatusKind s, fmi1String*  value);

#endif // FMI1_H
