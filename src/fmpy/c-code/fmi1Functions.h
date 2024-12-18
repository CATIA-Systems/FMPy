#ifndef FMI1FUNCTIONS_H
#define FMI1FUNCTIONS_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

/* -------------------------------------------------------------------------
 * Combined FMI 1.0 Functions for Model Exchange & Co-Simulation
 * -------------------------------------------------------------------------*/

/* Type definitions */
typedef void*        fmi1Component;
typedef unsigned int fmi1ValueReference;
typedef double       fmi1Real;
typedef int          fmi1Integer;
typedef char         fmi1Boolean;
typedef const char*  fmi1String;

/* Values for fmi1Boolean  */
#define fmi1True  1
#define fmi1False 0

/* Undefined value for fmi1ValueReference (largest unsigned int value) */
#define fmi1UndefinedValueReference (fmi1ValueReference)(-1)


/* make sure all compiler use the same alignment policies for structures */
#if defined _MSC_VER || defined __GNUC__
#pragma pack(push,8)
#endif

typedef enum  {
    fmi1OK,
    fmi1Warning,
    fmi1Discard,
    fmi1Error,
    fmi1Fatal
} fmi1Status;

typedef enum {
    fmi1DoStepStatus,
    fmi1PendingStatus,
    fmi1LastSuccessfulTime
} fmi1StatusKind;

typedef void   (*fmi1CallbackLogger)        (fmi1Component c, fmi1String instanceName, fmi1Status status, fmi1String category, fmi1String message, ...);
typedef void*  (*fmi1CallbackAllocateMemory)(size_t nobj, size_t size);
typedef void   (*fmi1CallbackFreeMemory)    (void* obj);
typedef void   (*fmi1StepFinished)          (fmi1Component c, fmi1Status status);

typedef struct {
    fmi1CallbackLogger         logger;
    fmi1CallbackAllocateMemory allocateMemory;
    fmi1CallbackFreeMemory     freeMemory;
    fmi1StepFinished           stepFinished;
} fmi1CallbackFunctions;

typedef struct {
    fmi1Boolean iterationConverged;
    fmi1Boolean stateValueReferencesChanged;
    fmi1Boolean stateValuesChanged;
    fmi1Boolean terminateSimulation;
    fmi1Boolean upcomingTimeEvent;
    fmi1Real    nextEventTime;
} fmi1EventInfo;

/* reset alignment policy to the one set before reading this file */
#if defined _MSC_VER || defined __GNUC__
#pragma pack(pop)
#endif

/***************************************************
 Common Functions for FMI 1.0
****************************************************/
typedef fmi1Status    fmi1SetRealTYPE         (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, const fmi1Real    value[]);
typedef fmi1Status    fmi1SetIntegerTYPE      (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, const fmi1Integer value[]);
typedef fmi1Status    fmi1SetBooleanTYPE      (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, const fmi1Boolean value[]);
typedef fmi1Status    fmi1SetStringTYPE       (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, const fmi1String  value[]);
typedef fmi1Status    fmi1GetRealTYPE         (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, fmi1Real    value[]);
typedef fmi1Status    fmi1GetIntegerTYPE      (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, fmi1Integer value[]);
typedef fmi1Status    fmi1GetBooleanTYPE      (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, fmi1Boolean value[]);
typedef fmi1Status    fmi1GetStringTYPE       (fmi1Component c, const fmi1ValueReference vr[], size_t nvr, fmi1String  value[]);
typedef fmi1Status    fmi1SetDebugLoggingTYPE (fmi1Component c, fmi1Boolean loggingOn);

/***************************************************
 FMI 1.0 for Model Exchange Functions
****************************************************/
typedef const char*   fmi1GetModelTypesPlatformTYPE      ();
typedef const char*   fmi1GetVersionTYPE                 ();
typedef fmi1Component fmi1InstantiateModelTYPE           (fmi1String instanceName, fmi1String GUID, fmi1CallbackFunctions functions, fmi1Boolean loggingOn);
typedef void          fmi1FreeModelInstanceTYPE          (fmi1Component c);
typedef fmi1Status    fmi1SetTimeTYPE                    (fmi1Component c, fmi1Real time);
typedef fmi1Status    fmi1SetContinuousStatesTYPE        (fmi1Component c, const fmi1Real x[], size_t nx);
typedef fmi1Status    fmi1CompletedIntegratorStepTYPE    (fmi1Component c, fmi1Boolean* callEventUpdate);
typedef fmi1Status    fmi1InitializeTYPE                 (fmi1Component c, fmi1Boolean toleranceControlled, fmi1Real relativeTolerance, fmi1EventInfo* eventInfo);
typedef fmi1Status    fmi1GetDerivativesTYPE             (fmi1Component c, fmi1Real derivatives[], size_t nx);
typedef fmi1Status    fmi1GetEventIndicatorsTYPE         (fmi1Component c, fmi1Real eventIndicators[], size_t ni);
typedef fmi1Status    fmi1EventUpdateTYPE                (fmi1Component c, fmi1Boolean intermediateResults, fmi1EventInfo* eventInfo);
typedef fmi1Status    fmi1GetContinuousStatesTYPE        (fmi1Component c, fmi1Real states[], size_t nx);
typedef fmi1Status    fmi1GetNominalContinuousStatesTYPE (fmi1Component c, fmi1Real x_nominal[], size_t nx);
typedef fmi1Status    fmi1GetStateValueReferencesTYPE    (fmi1Component c, fmi1ValueReference vrx[], size_t nx);
typedef fmi1Status    fmi1TerminateTYPE                  (fmi1Component c);

/***************************************************
 FMI 1.0 for Co-Simulation Functions
****************************************************/
typedef const char*   fmi1GetTypesPlatformTYPE         ();
typedef fmi1Component fmi1InstantiateSlaveTYPE         (fmi1String  instanceName, fmi1String  fmuGUID, fmi1String  fmuLocation,fmi1String  mimeType, fmi1Real timeout, fmi1Boolean visible, fmi1Boolean interactive, fmi1CallbackFunctions functions, fmi1Boolean loggingOn);
typedef fmi1Status    fmi1InitializeSlaveTYPE          (fmi1Component c, fmi1Real tStart, fmi1Boolean StopTimeDefined, fmi1Real tStop);
typedef fmi1Status    fmi1TerminateSlaveTYPE           (fmi1Component c);
typedef fmi1Status    fmi1ResetSlaveTYPE               (fmi1Component c);
typedef void          fmi1FreeSlaveInstanceTYPE        (fmi1Component c);
typedef fmi1Status    fmi1SetRealInputDerivativesTYPE  (fmi1Component c, const  fmi1ValueReference vr[], size_t nvr, const fmi1Integer order[], const  fmi1Real value[]);
typedef fmi1Status    fmi1GetRealOutputDerivativesTYPE (fmi1Component c, const fmi1ValueReference vr[], size_t  nvr, const fmi1Integer order[], fmi1Real value[]);
typedef fmi1Status    fmi1CancelStepTYPE               (fmi1Component c);
typedef fmi1Status    fmi1DoStepTYPE                   (fmi1Component c, fmi1Real currentCommunicationPoint, fmi1Real communicationStepSize, fmi1Boolean newStep);
typedef fmi1Status    fmi1GetStatusTYPE                (fmi1Component c, const fmi1StatusKind s, fmi1Status*  value);
typedef fmi1Status    fmi1GetRealStatusTYPE            (fmi1Component c, const fmi1StatusKind s, fmi1Real*    value);
typedef fmi1Status    fmi1GetIntegerStatusTYPE         (fmi1Component c, const fmi1StatusKind s, fmi1Integer* value);
typedef fmi1Status    fmi1GetBooleanStatusTYPE         (fmi1Component c, const fmi1StatusKind s, fmi1Boolean* value);
typedef fmi1Status    fmi1GetStringStatusTYPE          (fmi1Component c, const fmi1StatusKind s, fmi1String*  value);

#endif // FMI1FUNCTIONS_H
