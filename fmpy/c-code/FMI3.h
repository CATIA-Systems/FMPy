#ifndef FMI3_H
#define FMI3_H

/**************************************************************
 *  Copyright (c) Modelica Association Project "FMI".         *
 *  All rights reserved.                                      *
 *  This file is part of the Reference FMUs. See LICENSE.txt  *
 *  in the project root for license information.              *
 **************************************************************/

#ifdef __cplusplus
extern "C" {
#endif

#include "fmi3FunctionTypes.h"
#include "FMI.h"

struct FMI3Functions_ {

    fmi3Boolean discreteStatesNeedUpdate;
    fmi3Boolean terminateSimulation;
    fmi3Boolean nominalsOfContinuousStatesChanged;
    fmi3Boolean valuesOfContinuousStatesChanged;
    fmi3Boolean nextEventTimeDefined;
    fmi3Float64 nextEventTime;

    /***************************************************
    Common Functions for FMI 3.0
    ****************************************************/

    /* Inquire version numbers and set debug logging */
    fmi3GetVersionTYPE                      *fmi3GetVersion;
    fmi3SetDebugLoggingTYPE                 *fmi3SetDebugLogging;

    /* Creation and destruction of FMU instances */
    fmi3InstantiateModelExchangeTYPE        *fmi3InstantiateModelExchange;
    fmi3InstantiateCoSimulationTYPE         *fmi3InstantiateCoSimulation;
    fmi3InstantiateScheduledExecutionTYPE   *fmi3InstantiateScheduledExecution;
    fmi3FreeInstanceTYPE                    *fmi3FreeInstance;

    /* Enter and exit initialization mode, terminate and reset */
    fmi3EnterInitializationModeTYPE         *fmi3EnterInitializationMode;
    fmi3ExitInitializationModeTYPE          *fmi3ExitInitializationMode;
    fmi3EnterEventModeTYPE                  *fmi3EnterEventMode;
    fmi3TerminateTYPE                       *fmi3Terminate;
    fmi3ResetTYPE                           *fmi3Reset;

    /* Getting and setting variable values */
    fmi3GetFloat32TYPE                      *fmi3GetFloat32;
    fmi3GetFloat64TYPE                      *fmi3GetFloat64;
    fmi3GetInt8TYPE                         *fmi3GetInt8;
    fmi3GetUInt8TYPE                        *fmi3GetUInt8;
    fmi3GetInt16TYPE                        *fmi3GetInt16;
    fmi3GetUInt16TYPE                       *fmi3GetUInt16;
    fmi3GetInt32TYPE                        *fmi3GetInt32;
    fmi3GetUInt32TYPE                       *fmi3GetUInt32;
    fmi3GetInt64TYPE                        *fmi3GetInt64;
    fmi3GetUInt64TYPE                       *fmi3GetUInt64;
    fmi3GetBooleanTYPE                      *fmi3GetBoolean;
    fmi3GetStringTYPE                       *fmi3GetString;
    fmi3GetBinaryTYPE                       *fmi3GetBinary;
    fmi3SetFloat32TYPE                      *fmi3SetFloat32;
    fmi3SetFloat64TYPE                      *fmi3SetFloat64;
    fmi3SetInt8TYPE                         *fmi3SetInt8;
    fmi3SetUInt8TYPE                        *fmi3SetUInt8;
    fmi3SetInt16TYPE                        *fmi3SetInt16;
    fmi3SetUInt16TYPE                       *fmi3SetUInt16;
    fmi3SetInt32TYPE                        *fmi3SetInt32;
    fmi3SetUInt32TYPE                       *fmi3SetUInt32;
    fmi3SetInt64TYPE                        *fmi3SetInt64;
    fmi3SetUInt64TYPE                       *fmi3SetUInt64;
    fmi3SetBooleanTYPE                      *fmi3SetBoolean;
    fmi3SetStringTYPE                       *fmi3SetString;
    fmi3SetBinaryTYPE                       *fmi3SetBinary;

    /* Getting Variable Dependency Information */
    fmi3GetNumberOfVariableDependenciesTYPE *fmi3GetNumberOfVariableDependencies;
    fmi3GetVariableDependenciesTYPE         *fmi3GetVariableDependencies;

    /* Getting and setting the internal FMU state */
    fmi3GetFMUStateTYPE                     *fmi3GetFMUState;
    fmi3SetFMUStateTYPE                     *fmi3SetFMUState;
    fmi3FreeFMUStateTYPE                    *fmi3FreeFMUState;
    fmi3SerializedFMUStateSizeTYPE          *fmi3SerializedFMUStateSize;
    fmi3SerializeFMUStateTYPE               *fmi3SerializeFMUState;
    fmi3DeSerializeFMUStateTYPE             *fmi3DeSerializeFMUState;

    /* Getting partial derivatives */
    fmi3GetDirectionalDerivativeTYPE        *fmi3GetDirectionalDerivative;
    fmi3GetAdjointDerivativeTYPE            *fmi3GetAdjointDerivative;

    /* Entering and exiting the Configuration or Reconfiguration Mode */
    fmi3EnterConfigurationModeTYPE          *fmi3EnterConfigurationMode;
    fmi3ExitConfigurationModeTYPE           *fmi3ExitConfigurationMode;

    /* Clock related functions */
    fmi3GetClockTYPE                        *fmi3GetClock;
    fmi3SetClockTYPE                        *fmi3SetClock;
    fmi3GetIntervalDecimalTYPE              *fmi3GetIntervalDecimal;
    fmi3GetIntervalFractionTYPE             *fmi3GetIntervalFraction;
    fmi3SetIntervalDecimalTYPE              *fmi3SetIntervalDecimal;
    fmi3SetIntervalFractionTYPE             *fmi3SetIntervalFraction;
    fmi3UpdateDiscreteStatesTYPE            *fmi3UpdateDiscreteStates;

    /***************************************************
    Functions for FMI 3.0 for Model Exchange
    ****************************************************/

    fmi3EnterContinuousTimeModeTYPE         *fmi3EnterContinuousTimeMode;
    fmi3CompletedIntegratorStepTYPE         *fmi3CompletedIntegratorStep;

    /* Providing independent variables and re-initialization of caching */
    fmi3SetTimeTYPE                         *fmi3SetTime;
    fmi3SetContinuousStatesTYPE             *fmi3SetContinuousStates;

    /* Evaluation of the model equations */
    fmi3GetContinuousStateDerivativesTYPE   *fmi3GetContinuousStateDerivatives;
    fmi3GetEventIndicatorsTYPE              *fmi3GetEventIndicators;
    fmi3GetContinuousStatesTYPE             *fmi3GetContinuousStates;
    fmi3GetNominalsOfContinuousStatesTYPE   *fmi3GetNominalsOfContinuousStates;
    fmi3GetNumberOfEventIndicatorsTYPE      *fmi3GetNumberOfEventIndicators;
    fmi3GetNumberOfContinuousStatesTYPE     *fmi3GetNumberOfContinuousStates;

    /***************************************************
    Functions for FMI 3.0 for Co-Simulation
    ****************************************************/

    /* Simulating the FMU */
    fmi3EnterStepModeTYPE                   *fmi3EnterStepMode;
    fmi3GetOutputDerivativesTYPE            *fmi3GetOutputDerivatives;
    fmi3DoStepTYPE                          *fmi3DoStep;
    fmi3ActivateModelPartitionTYPE          *fmi3ActivateModelPartition;

};


/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers and setting logging status */
FMI_STATIC const char* FMI3GetVersion(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3SetDebugLogging(FMIInstance *instance,
    fmi3Boolean loggingOn,
    size_t nCategories,
    const fmi3String categories[]);

/* Creation and destruction of FMU instances and setting debug status */
FMI_STATIC fmi3Status FMI3InstantiateModelExchange(
    FMIInstance *instance,
    fmi3String   instantiationToken,
    fmi3String   resourceLocation,
    fmi3Boolean  visible,
    fmi3Boolean  loggingOn);

FMI_STATIC fmi3Status FMI3InstantiateCoSimulation(
    FMIInstance                   *instance,
    fmi3String                     instantiationToken,
    fmi3String                     resourcePath,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    eventModeUsed,
    fmi3Boolean                    earlyReturnAllowed,
    const fmi3ValueReference       requiredIntermediateVariables[],
    size_t                         nRequiredIntermediateVariables,
    fmi3CallbackIntermediateUpdate intermediateUpdate);

FMI_STATIC fmi3Status FMI3InstantiateScheduledExecution(
    FMIInstance                   *instance,
    fmi3String                     instantiationToken,
    fmi3String                     resourceLocation,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    const fmi3ValueReference       requiredIntermediateVariables[],
    size_t                         nRequiredIntermediateVariables,
    fmi3CallbackIntermediateUpdate intermediateUpdate,
    fmi3CallbackLockPreemption     lockPreemption,
    fmi3CallbackUnlockPreemption   unlockPreemption);

FMI_STATIC fmi3Status FMI3FreeInstance(FMIInstance *instance);

/* Enter and exit initialization mode, enter event mode, terminate and reset */
FMI_STATIC fmi3Status FMI3EnterInitializationMode(FMIInstance *instance,
    fmi3Boolean toleranceDefined,
    fmi3Float64 tolerance,
    fmi3Float64 startTime,
    fmi3Boolean stopTimeDefined,
    fmi3Float64 stopTime);

FMI_STATIC fmi3Status FMI3ExitInitializationMode(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3EnterEventMode(FMIInstance *instance,
    fmi3Boolean stepEvent,
    fmi3Boolean stateEvent,
    const fmi3Int32 rootsFound[],
    size_t nEventIndicators,
    fmi3Boolean timeEvent);

FMI_STATIC fmi3Status FMI3Terminate(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3Reset(FMIInstance *instance);

/* Getting and setting variable values */
FMI_STATIC fmi3Status FMI3GetFloat32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetFloat64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int8 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetUInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt8 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int16 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetUInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt16 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetUInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetUInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetBoolean(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Boolean values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetString(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3String values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetBinary(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    size_t sizes[],
    fmi3Binary values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3GetClock(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Clock values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetFloat32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetFloat64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int8 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetUInt8(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt8 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int16 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetUInt16(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt16 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetUInt32(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt32 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetUInt64(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetBoolean(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Boolean values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetString(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3String values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetBinary(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const size_t sizes[],
    const fmi3Binary values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3SetClock(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Clock values[],
    size_t nValues);

/* Getting Variable Dependency Information */
FMI_STATIC fmi3Status FMI3GetNumberOfVariableDependencies(FMIInstance *instance,
    fmi3ValueReference valueReference,
    size_t* nDependencies);

FMI_STATIC fmi3Status FMI3GetVariableDependencies(FMIInstance *instance,
    fmi3ValueReference dependent,
    size_t elementIndicesOfDependent[],
    fmi3ValueReference independents[],
    size_t elementIndicesOfIndependents[],
    fmi3DependencyKind dependencyKinds[],
    size_t nDependencies);

/* Getting and setting the internal FMU state */
FMI_STATIC fmi3Status FMI3GetFMUState(FMIInstance *instance, fmi3FMUState* FMUState);

FMI_STATIC fmi3Status FMI3SetFMUState(FMIInstance *instance, fmi3FMUState  FMUState);

FMI_STATIC fmi3Status FMI3FreeFMUState(FMIInstance *instance, fmi3FMUState* FMUState);

FMI_STATIC fmi3Status FMI3SerializedFMUStateSize(FMIInstance *instance,
    fmi3FMUState  FMUState,
    size_t* size);

FMI_STATIC fmi3Status FMI3SerializeFMUState(FMIInstance *instance,
    fmi3FMUState  FMUState,
    fmi3Byte serializedState[],
    size_t size);

FMI_STATIC fmi3Status FMI3DeSerializeFMUState(FMIInstance *instance,
    const fmi3Byte serializedState[],
    size_t size,
    fmi3FMUState* FMUState);

/* Getting partial derivatives */
FMI_STATIC fmi3Status FMI3GetDirectionalDerivative(FMIInstance *instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity);

FMI_STATIC fmi3Status FMI3GetAdjointDerivative(FMIInstance *instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity);

/* Entering and exiting the Configuration or Reconfiguration Mode */
FMI_STATIC fmi3Status FMI3EnterConfigurationMode(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3ExitConfigurationMode(FMIInstance *instance);

/* Clock related functions */
FMI_STATIC fmi3Status FMI3GetIntervalDecimal(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 intervals[],
    fmi3IntervalQualifier qualifiers[],
    size_t nIntervals);

//fmi3Status FMI3GetIntervalFraction(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    fmi3UInt64 intervalCounter[],
//    fmi3UInt64 resolution[],
//    size_t nValues);
//
//fmi3Status FMI3SetIntervalDecimal(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    const fmi3Float64 interval[],
//    size_t nValues);
//
//fmi3Status FMI3SetIntervalFraction(FMIInstance *instance,
//    const fmi3ValueReference valueReferences[],
//    size_t nValueReferences,
//    const fmi3UInt64 intervalCounter[],
//    const fmi3UInt64 resolution[],
//    size_t nValues);

FMI_STATIC fmi3Status FMI3UpdateDiscreteStates(FMIInstance *instance,
    fmi3Boolean *discreteStatesNeedUpdate,
    fmi3Boolean *terminateSimulation,
    fmi3Boolean *nominalsOfContinuousStatesChanged,
    fmi3Boolean *valuesOfContinuousStatesChanged,
    fmi3Boolean *nextEventTimeDefined,
    fmi3Float64 *nextEventTime);

/***************************************************
Types for Functions for Model Exchange
****************************************************/

FMI_STATIC fmi3Status FMI3EnterContinuousTimeMode(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3CompletedIntegratorStep(FMIInstance *instance,
    fmi3Boolean noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* enterEventMode,
    fmi3Boolean* terminateSimulation);

/* Providing independent variables and re-initialization of caching */
FMI_STATIC fmi3Status FMI3SetTime(FMIInstance *instance, fmi3Float64 time);

FMI_STATIC fmi3Status FMI3SetContinuousStates(FMIInstance *instance,
    const fmi3Float64 continuousStates[],
    size_t nContinuousStates);

/* Evaluation of the model equations */
FMI_STATIC fmi3Status FMI3GetContinuousStateDerivatives(FMIInstance *instance,
    fmi3Float64 derivatives[],
    size_t nContinuousStates);

FMI_STATIC fmi3Status FMI3GetEventIndicators(FMIInstance *instance,
    fmi3Float64 eventIndicators[],
    size_t nEventIndicators);

FMI_STATIC fmi3Status FMI3GetContinuousStates(FMIInstance *instance,
    fmi3Float64 continuousStates[],
    size_t nContinuousStates);

FMI_STATIC fmi3Status FMI3GetNominalsOfContinuousStates(FMIInstance *instance,
    fmi3Float64 nominals[],
    size_t nContinuousStates);

FMI_STATIC fmi3Status FMI3GetNumberOfEventIndicators(FMIInstance *instance,
    size_t* nEventIndicators);

FMI_STATIC fmi3Status FMI3GetNumberOfContinuousStates(FMIInstance *instance,
    size_t* nContinuousStates);

/***************************************************
Types for Functions for Co-Simulation
****************************************************/

/* Simulating the FMU */

FMI_STATIC fmi3Status FMI3EnterStepMode(FMIInstance *instance);

FMI_STATIC fmi3Status FMI3GetOutputDerivatives(FMIInstance *instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 orders[],
    fmi3Float64 values[],
    size_t nValues);

FMI_STATIC fmi3Status FMI3DoStep(FMIInstance *instance,
    fmi3Float64 currentCommunicationPoint,
    fmi3Float64 communicationStepSize,
    fmi3Boolean noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* eventEncountered,
    fmi3Boolean* terminate,
    fmi3Boolean* earlyReturn,
    fmi3Float64* lastSuccessfulTime);

FMI_STATIC fmi3Status FMI3ActivateModelPartition(FMIInstance *instance,
    fmi3ValueReference clockReference,
    size_t clockElementIndex,
    fmi3Float64 activationTime);

#ifdef __cplusplus
}  /* end of extern "C" { */
#endif

#endif // FMI3_H
