#ifndef fmi3FunctionTypes_h
#define fmi3FunctionTypes_h

#include "fmi3PlatformTypes.h"

/*
This header file must be utilized when compiling an FMU or an FMI master.
It declares data and function types for FMI 3.0-alpha.1.

Copyright (C) 2011 MODELISAR consortium,
              2012-2019 Modelica Association Project "FMI"
              All rights reserved.

This file is licensed by the copyright holders under the 2-Clause BSD License
(https://opensource.org/licenses/BSD-2-Clause):

----------------------------------------------------------------------------
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
 this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright notice,
 this list of conditions and the following disclaimer in the documentation
 and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
----------------------------------------------------------------------------
*/

#ifdef __cplusplus
extern "C" {
#endif

/* Include stddef.h, in order that size_t etc. is defined */
#include <stddef.h>


/* Type definitions */

/* tag::Status[] */
typedef enum {
    fmi3OK,
    fmi3Warning,
    fmi3Discard,
    fmi3Error,
    fmi3Fatal,
} fmi3Status;
/* end::Status[] */

/* tag::DependencyKind[] */
typedef enum {
    /* fmi3Independent = 0, not needed but reserved for future use */
    fmi3Constant  = 1,
    fmi3Fixed     = 2,
    fmi3Tunable   = 3,
    fmi3Discrete  = 4,
    fmi3Dependent = 5
} fmi3DependencyKind;
/* end::DependencyKind[] */

/* tag::CallbackFunctions[] */
typedef void  (*fmi3CallbackLogMessage)     (fmi3InstanceEnvironment instanceEnvironment,
                                             fmi3String instanceName,
                                             fmi3Status status,
                                             fmi3String category,
                                             fmi3String message);
typedef void* (*fmi3CallbackAllocateMemory) (fmi3InstanceEnvironment instanceEnvironment,
                                             size_t nobj,
                                             size_t size);
typedef void  (*fmi3CallbackFreeMemory)     (fmi3InstanceEnvironment instanceEnvironment,
                                             void* obj);
/* end::CallbackFunctions[] */

/* tag::CallbackIntermediateUpdate[] */
typedef fmi3Status (*fmi3CallbackIntermediateUpdate) (
  fmi3InstanceEnvironment instanceEnvironment,
  fmi3Float64 intermediateUpdateTime,
  fmi3Boolean eventOccurred,
  fmi3Boolean clocksTicked,
  fmi3Boolean intermediateVariableSetAllowed,
  fmi3Boolean intermediateVariableGetAllowed,
  fmi3Boolean intermediateStepFinished,
  fmi3Boolean canReturnEarly);
/* end::CallbackIntermediateUpdate[] */

/* tag::PreemptionLock[] */
typedef void       (*fmi3CallbackLockPreemption)   ();
typedef void       (*fmi3CallbackUnlockPreemption) ();
/* end::PreemptionLock[] */

/* Define fmi3 function pointer types to simplify dynamic loading */

/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers and setting logging status */
/* tag::GetVersion[] */
typedef const char* fmi3GetVersionTYPE(void);
/* end::GetVersion[] */

/* tag::SetDebugLogging[] */
typedef fmi3Status  fmi3SetDebugLoggingTYPE(fmi3Instance instance,
                                            fmi3Boolean loggingOn,
                                            size_t nCategories,
                                            const fmi3String categories[]);
/* end::SetDebugLogging[] */

/* Creation and destruction of FMU instances and setting debug status */
/* tag::Instantiate[] */
typedef fmi3Instance fmi3InstantiateModelExchangeTYPE(
    fmi3String                 instanceName,
    fmi3String                 instantiationToken,
    fmi3String                 resourceLocation,
    fmi3Boolean                visible,
    fmi3Boolean                loggingOn,
    fmi3InstanceEnvironment    instanceEnvironment,
    fmi3CallbackLogMessage     logMessage,
    fmi3CallbackAllocateMemory allocateMemory,
    fmi3CallbackFreeMemory     freeMemory);

typedef fmi3Instance fmi3InstantiateBasicCoSimulationTYPE(
    fmi3String                     instanceName,
    fmi3String                     instantiationToken,
    fmi3String                     resourceLocation,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    intermediateVariableGetRequired,
    fmi3Boolean                    intermediateInternalVariableGetRequired,
    fmi3Boolean                    intermediateVariableSetRequired,
    fmi3InstanceEnvironment        instanceEnvironment,
    fmi3CallbackLogMessage         logMessage,
    fmi3CallbackAllocateMemory     allocateMemory,
    fmi3CallbackFreeMemory         freeMemory,
    fmi3CallbackIntermediateUpdate intermediateUpdate);

typedef fmi3Instance fmi3InstantiateHybridCoSimulationTYPE(
    fmi3String                     instanceName,
    fmi3String                     instantiationToken,
    fmi3String                     resourceLocation,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    intermediateVariableGetRequired,
    fmi3Boolean                    intermediateInternalVariableGetRequired,
    fmi3Boolean                    intermediateVariableSetRequired,
    fmi3InstanceEnvironment        instanceEnvironment,
    fmi3CallbackLogMessage         logMessage,
    fmi3CallbackAllocateMemory     allocateMemory,
    fmi3CallbackFreeMemory         freeMemory,
    fmi3CallbackIntermediateUpdate intermediateUpdate);

typedef fmi3Instance fmi3InstantiateScheduledCoSimulationTYPE(
    fmi3String                     instanceName,
    fmi3String                     instantiationToken,
    fmi3String                     resourceLocation,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    intermediateVariableGetRequired,
    fmi3Boolean                    intermediateInternalVariableGetRequired,
    fmi3Boolean                    intermediateVariableSetRequired,
    fmi3InstanceEnvironment        instanceEnvironment,
    fmi3CallbackLogMessage         logMessage,
    fmi3CallbackAllocateMemory     allocateMemory,
    fmi3CallbackFreeMemory         freeMemory,
    fmi3CallbackIntermediateUpdate intermediateUpdate,
    fmi3CallbackLockPreemption     lockPreemption,
    fmi3CallbackUnlockPreemption   unlockPreemption);
/* end::Instantiate[] */

/* tag::FreeInstance[] */
typedef void fmi3FreeInstanceTYPE(fmi3Instance instance);
/* end::FreeInstance[] */

/* Enter and exit initialization mode, enter event mode, terminate and reset */
/* tag::SetupExperiment[] */
typedef fmi3Status fmi3SetupExperimentTYPE(fmi3Instance instance,
                                           fmi3Boolean toleranceDefined,
                                           fmi3Float64 tolerance,
                                           fmi3Float64 startTime,
                                           fmi3Boolean stopTimeDefined,
                                           fmi3Float64 stopTime);
/* end::SetupExperiment[] */

/* tag::EnterInitializationMode[] */
typedef fmi3Status fmi3EnterInitializationModeTYPE(fmi3Instance instance);
/* end::EnterInitializationMode[] */

/* tag::ExitInitializationMode[] */
typedef fmi3Status fmi3ExitInitializationModeTYPE(fmi3Instance instance);
/* end::ExitInitializationMode[] */

/* tag::EnterEventMode[] */
typedef fmi3Status fmi3EnterEventModeTYPE(fmi3Instance instance,
                                          fmi3Boolean inputEvent,
                                          fmi3Boolean stepEvent,
                                          const fmi3Int32 rootsFound[],
                                          size_t nEventIndicators,
                                          fmi3Boolean timeEvent);
/* end::EnterEventMode[] */

/* tag::Terminate[] */
typedef fmi3Status fmi3TerminateTYPE(fmi3Instance instance);
/* end::Terminate[] */

/* tag::Reset[] */
typedef fmi3Status fmi3ResetTYPE(fmi3Instance instance);
/* end::Reset[] */

/* Getting and setting variable values */
/* tag::Getters[] */
typedef fmi3Status fmi3GetFloat32TYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Float32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetFloat64TYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Float64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetInt8TYPE   (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Int8 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetUInt8TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3UInt8 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetInt16TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Int16 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetUInt16TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3UInt16 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetInt32TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Int32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetUInt32TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3UInt32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetInt64TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Int64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetUInt64TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3UInt64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetBooleanTYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3Boolean values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetStringTYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      fmi3String values[],
                                      size_t nValues);

typedef fmi3Status fmi3GetBinaryTYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      size_t sizes[],
                                      fmi3Binary values[],
                                      size_t nValues);
/* end::Getters[] */

/* tag::Setters[] */
typedef fmi3Status fmi3SetFloat32TYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Float32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetFloat64TYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Float64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetInt8TYPE   (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Int8 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetUInt8TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3UInt8 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetInt16TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Int16 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetUInt16TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3UInt16 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetInt32TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Int32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetUInt32TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3UInt32 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetInt64TYPE  (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Int64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetUInt64TYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3UInt64 values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetBooleanTYPE(fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3Boolean values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetStringTYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const fmi3String values[],
                                      size_t nValues);

typedef fmi3Status fmi3SetBinaryTYPE (fmi3Instance instance,
                                      const fmi3ValueReference valueReferences[],
                                      size_t nValueReferences,
                                      const size_t sizes[],
                                      const fmi3Binary values[],
                                      size_t nValues);
/* end::Setters[] */

/* Getting Variable Dependency Information */
/* tag::GetNumberOfVariableDependencies[] */
typedef fmi3Status fmi3GetNumberOfVariableDependenciesTYPE(fmi3Instance instance,
                                                           fmi3ValueReference valueReference,
                                                           size_t* nDependencies);
/* end::GetNumberOfVariableDependencies[] */

/* tag::GetVariableDependencies[] */
typedef fmi3Status fmi3GetVariableDependenciesTYPE(fmi3Instance instance,
                                                   fmi3ValueReference dependent,
                                                   size_t elementIndicesOfDependent[],
                                                   fmi3ValueReference independents[],
                                                   size_t elementIndicesOfIndependents[],
                                                   fmi3DependencyKind dependencyKinds[],
                                                   size_t nDependencies);
/* end::GetVariableDependencies[] */

/* Getting and setting the internal FMU state */
/* tag::GetFMUState[] */
typedef fmi3Status fmi3GetFMUStateTYPE (fmi3Instance instance, fmi3FMUState* FMUState);
/* end::GetFMUState[] */

/* tag::SetFMUState[] */
typedef fmi3Status fmi3SetFMUStateTYPE (fmi3Instance instance, fmi3FMUState  FMUState);
/* end::SetFMUState[] */

/* tag::FreeFMUState[] */
typedef fmi3Status fmi3FreeFMUStateTYPE(fmi3Instance instance, fmi3FMUState* FMUState);
/* end::FreeFMUState[] */

/* tag::SerializedFMUState[] */
typedef fmi3Status fmi3SerializedFMUStateSizeTYPE(fmi3Instance instance,
                                                  fmi3FMUState  FMUState,
                                                  size_t* size);

typedef fmi3Status fmi3SerializeFMUStateTYPE     (fmi3Instance instance,
                                                  fmi3FMUState  FMUState,
                                                  fmi3Byte serializedState[],
                                                  size_t size);

typedef fmi3Status fmi3DeSerializeFMUStateTYPE   (fmi3Instance instance,
                                                  const fmi3Byte serializedState[],
                                                  size_t size,
                                                  fmi3FMUState* FMUState);
/* end::SerializedFMUState[] */

/* Getting partial derivatives */
/* tag::GetDirectionalDerivative[] */
typedef fmi3Status fmi3GetDirectionalDerivativeTYPE(fmi3Instance instance,
                                                    const fmi3ValueReference unknowns[],
                                                    size_t nUnknowns,
                                                    const fmi3ValueReference knowns[],
                                                    size_t nKnowns,
                                                    const fmi3Float64 seed[],
                                                    size_t nSeed,
                                                    fmi3Float64 sensitivity[],
                                                    size_t nSensitivity);
/* end::GetDirectionalDerivative[] */

/* tag::GetAdjointDerivative[] */
typedef fmi3Status fmi3GetAdjointDerivativeTYPE(fmi3Instance instance,
                                                const fmi3ValueReference unknowns[],
                                                size_t nUnknowns,
                                                const fmi3ValueReference knowns[],
                                                size_t nKnowns,
                                                const fmi3Float64 seed[],
                                                size_t nSeed,
                                                fmi3Float64 sensitivity[],
                                                size_t nSensitivity);
/* end::GetAdjointDerivative[] */



/* Entering and exiting the Configuration or Reconfiguration Mode */
/* tag::EnterConfigurationMode[] */
typedef fmi3Status fmi3EnterConfigurationModeTYPE(fmi3Instance instance);
/* end::EnterConfigurationMode[] */

/* tag::ExitConfigurationMode[] */
typedef fmi3Status fmi3ExitConfigurationModeTYPE(fmi3Instance instance);
/* end::ExitConfigurationMode[] */

/* Clock related functions */
/* tag::GetClock[] */
typedef fmi3Status fmi3GetClockTYPE(fmi3Instance instance,
                                    const fmi3ValueReference valueReferences[],
                                    size_t nValueReferences,
                                    fmi3Clock values[]);
/* end::GetClock[] */

/* tag::SetClock[] */
typedef fmi3Status fmi3SetClockTYPE(fmi3Instance instance,
                                    const fmi3ValueReference valueReferences[],
                                    size_t nValueReferences,
                                    const fmi3Clock values[],
                                    const fmi3Boolean subactive[]);
/* end::SetClock[] */

/* tag::GetIntervalDecimal[] */
typedef fmi3Status fmi3GetIntervalDecimalTYPE(fmi3Instance instance,
                                              const fmi3ValueReference valueReferences[],
                                              size_t nValueReferences,
                                              fmi3Float64 interval[]);
/* end::GetIntervalDecimal[] */

/* tag::GetIntervalFraction[] */
typedef fmi3Status fmi3GetIntervalFractionTYPE(fmi3Instance instance,
                                               const fmi3ValueReference valueReferences[],
                                               size_t nValueReferences,
                                               fmi3UInt64 intervalCounter[],
                                               fmi3UInt64 resolution[]);
/* end::GetIntervalFraction[] */

/* tag::SetIntervalDecimal[] */
typedef fmi3Status fmi3SetIntervalDecimalTYPE(fmi3Instance instance,
                                              const fmi3ValueReference valueReferences[],
                                              size_t nValueReferences,
                                              const fmi3Float64 interval[]);
/* end::SetIntervalDecimal[] */

/* tag::SetIntervalFraction[] */
typedef fmi3Status fmi3SetIntervalFractionTYPE(fmi3Instance instance,
                                               const fmi3ValueReference valueReferences[],
                                               size_t nValueReferences,
                                               const fmi3UInt64 intervalCounter[],
                                               const fmi3UInt64 resolution[]);
/* end::SetIntervalFraction[] */

/* tag::NewDiscreteStates[] */
typedef fmi3Status fmi3NewDiscreteStatesTYPE(fmi3Instance instance,
                                             fmi3Boolean *newDiscreteStatesNeeded,
                                             fmi3Boolean *terminateSimulation,
                                             fmi3Boolean *nominalsOfContinuousStatesChanged,
                                             fmi3Boolean *valuesOfContinuousStatesChanged,
                                             fmi3Boolean *nextEventTimeDefined,
                                             fmi3Float64 *nextEventTime);
/* end::NewDiscreteStates[] */

/***************************************************
Types for Functions for Model Exchange
****************************************************/

/* tag::EnterContinuousTimeMode[] */
typedef fmi3Status fmi3EnterContinuousTimeModeTYPE(fmi3Instance instance);
/* end::EnterContinuousTimeMode[] */

/* tag::CompletedIntegratorStep[] */
typedef fmi3Status fmi3CompletedIntegratorStepTYPE(fmi3Instance instance,
                                                   fmi3Boolean noSetFMUStatePriorToCurrentPoint,
                                                   fmi3Boolean* enterEventMode,
                                                   fmi3Boolean* terminateSimulation);
/* end::CompletedIntegratorStep[] */

/* Providing independent variables and re-initialization of caching */
/* tag::SetTime[] */
typedef fmi3Status fmi3SetTimeTYPE(fmi3Instance instance, fmi3Float64 time);
/* end::SetTime[] */

/* tag::SetContinuousStates[] */
typedef fmi3Status fmi3SetContinuousStatesTYPE(fmi3Instance instance,
                                               const fmi3Float64 x[],
                                               size_t nx);
/* end::SetContinuousStates[] */

/* Evaluation of the model equations */
/* tag::GetDerivatives[] */
typedef fmi3Status fmi3GetDerivativesTYPE(fmi3Instance instance,
                                          fmi3Float64 derivatives[],
                                          size_t nx);
/* end::GetDerivatives[] */

/* tag::GetEventIndicators[] */
typedef fmi3Status fmi3GetEventIndicatorsTYPE(fmi3Instance instance,
                                              fmi3Float64 eventIndicators[],
                                              size_t ni);
/* end::GetEventIndicators[] */

/* tag::GetContinuousStates[] */
typedef fmi3Status fmi3GetContinuousStatesTYPE(fmi3Instance instance, fmi3Float64 x[], size_t nx);
/* end::GetContinuousStates[] */

/* tag::GetNominalsOfContinuousStates[] */
typedef fmi3Status fmi3GetNominalsOfContinuousStatesTYPE(fmi3Instance instance,
                                                         fmi3Float64 nominals[],
                                                         size_t nx);
/* end::GetNominalsOfContinuousStates[] */

/* tag::GetNumberOfEventIndicators[] */
typedef fmi3Status fmi3GetNumberOfEventIndicatorsTYPE(fmi3Instance instance, size_t* nz);
/* end::GetNumberOfEventIndicators[] */

/* tag::GetNumberOfContinuousStates[] */
typedef fmi3Status fmi3GetNumberOfContinuousStatesTYPE(fmi3Instance instance, size_t* nx);
/* end::GetNumberOfContinuousStates[] */

/***************************************************
Types for Functions for Co-Simulation
****************************************************/

/* Simulating the slave */

/* tag::EnterStepMode[] */
typedef fmi3Status fmi3EnterStepModeTYPE(fmi3Instance instance);
/* end::EnterStepMode[] */

/* tag::SetInputDerivatives[] */
typedef fmi3Status fmi3SetInputDerivativesTYPE(fmi3Instance instance,
                                               const fmi3ValueReference valueReferences[],
                                               size_t nValueReferences,
                                               const fmi3Int32 orders[],
                                               const fmi3Float64 values[],
                                               size_t nValues);
/* end::SetInputDerivatives[] */

/* tag::GetOutputDerivatives[] */
typedef fmi3Status fmi3GetOutputDerivativesTYPE(fmi3Instance instance,
                                                const fmi3ValueReference valueReferences[],
                                                size_t nValueReferences,
                                                const fmi3Int32 orders[],
                                                fmi3Float64 values[],
                                                size_t nValues);
/* end::GetOutputDerivatives[] */

/* tag::DoStep[] */
typedef fmi3Status fmi3DoStepTYPE(fmi3Instance instance,
                                  fmi3Float64 currentCommunicationPoint,
                                  fmi3Float64 communicationStepSize,
                                  fmi3Boolean noSetFMUStatePriorToCurrentPoint,
                                  fmi3Boolean* earlyReturn);
/* end::DoStep[] */

/* tag::ActivateModelPartition[] */
typedef fmi3Status fmi3ActivateModelPartitionTYPE(fmi3Instance instance,
                                                  fmi3ValueReference clockReference,
                                                  fmi3Float64 activationTime);
/* end::ActivateModelPartition[] */

/* tag::DoEarlyReturn[] */
typedef fmi3Status fmi3DoEarlyReturnTYPE(fmi3Instance instance, fmi3Float64 earlyReturnTime);
/* end::DoEarlyReturn[] */

/* tag::GetDoStepDiscardedStatus[] */
typedef fmi3Status fmi3GetDoStepDiscardedStatusTYPE(fmi3Instance instance,
                                                    fmi3Boolean* terminate,
                                                    fmi3Float64* lastSuccessfulTime);
/* end::GetDoStepDiscardedStatus[] */

#ifdef __cplusplus
}  /* end of extern "C" { */
#endif

#endif /* fmi3FunctionTypes_h */
