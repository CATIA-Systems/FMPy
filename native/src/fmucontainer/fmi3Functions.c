#include "fmi3Functions.h"
#include "FMUContainer.h"
#include "FMI2.h"


#define GET_SYSTEM \
    FMIStatus status = FMIOK; \
    System *s = (System *)instance; \
    if (!s) return fmi3Error

#define NOT_IMPLEMENTED \
    return fmi3Error


const char* fmi3GetVersion(void) {
    return fmi3Version;
}

fmi3Status fmi3SetDebugLogging(fmi3Instance instance,
    fmi3Boolean loggingOn,
    size_t nCategories,
    const fmi3String categories[]) {
    NOT_IMPLEMENTED;
}

fmi3Instance fmi3InstantiateModelExchange(
    fmi3String                 instanceName,
    fmi3String                 instantiationToken,
    fmi3String                 resourcePath,
    fmi3Boolean                visible,
    fmi3Boolean                loggingOn,
    fmi3InstanceEnvironment    instanceEnvironment,
    fmi3LogMessageCallback     logMessage) {
    return NULL;
}

fmi3Instance fmi3InstantiateCoSimulation(
    fmi3String                     instanceName,
    fmi3String                     instantiationToken,
    fmi3String                     resourcePath,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3Boolean                    eventModeUsed,
    fmi3Boolean                    earlyReturnAllowed,
    const fmi3ValueReference       requiredIntermediateVariables[],
    size_t                         nRequiredIntermediateVariables,
    fmi3InstanceEnvironment        instanceEnvironment,
    fmi3LogMessageCallback         logMessage,
    fmi3IntermediateUpdateCallback intermediateUpdate) {

    return instantiateSystem(FMIVersion3, resourcePath, instanceName, logMessage, instanceEnvironment, loggingOn, visible);
}

fmi3Instance fmi3InstantiateScheduledExecution(
    fmi3String                     instanceName,
    fmi3String                     instantiationToken,
    fmi3String                     resourcePath,
    fmi3Boolean                    visible,
    fmi3Boolean                    loggingOn,
    fmi3InstanceEnvironment        instanceEnvironment,
    fmi3LogMessageCallback         logMessage,
    fmi3ClockUpdateCallback        clockUpdate,
    fmi3LockPreemptionCallback     lockPreemption,
    fmi3UnlockPreemptionCallback   unlockPreemption) {
    return NULL;
}

void fmi3FreeInstance(fmi3Instance instance) {

    if (instance) {
        freeSystem((System*)instance);
    }
}

fmi3Status fmi3EnterInitializationMode(fmi3Instance instance,
    fmi3Boolean toleranceDefined,
    fmi3Float64 tolerance,
    fmi3Float64 startTime,
    fmi3Boolean stopTimeDefined,
    fmi3Float64 stopTime) {

    System* s = (System*)instance;

    s->time = startTime;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        status = FMI2SetupExperiment(m, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime);
        status = FMI2EnterInitializationMode(m);
    }

    return status;
}

fmi3Status fmi3ExitInitializationMode(fmi3Instance instance) {

    GET_SYSTEM;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        status = FMI2ExitInitializationMode(m);
    }

    return status;
}

fmi3Status fmi3EnterEventMode(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3Terminate(fmi3Instance instance) { 
    
    GET_SYSTEM;

    return terminateSystem(s);
}

fmi3Status fmi3Reset(fmi3Instance instance) { 

    GET_SYSTEM;

    return resetSystem(s);
}

fmi3Status fmi3GetFloat32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float32 values[],
    size_t nValues) {
    return fmi3Error;
}

fmi3Status fmi3GetFloat64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const fmi3ValueReference vr = valueReferences[i];

        if (vr == 0) {
            values[i] = s->time;
            continue;
        }

        const size_t j = vr - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        status = FMI2GetReal(m, &(vm.vr[0]), 1, &values[i]);
    }

    return status;
}

fmi3Status fmi3GetInt8(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int8 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetUInt8(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt8 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetInt16(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int16 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetUInt16(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt16 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetInt32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int32 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const fmi3ValueReference vr = valueReferences[i];

        const size_t j = vr - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        status = FMI2GetInteger(m, &(vm.vr[0]), 1, &values[i]);
    }

    return status;
}

fmi3Status fmi3GetUInt32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt32 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetInt64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Int64 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const fmi3ValueReference vr = valueReferences[i];

        const size_t j = vr - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        fmi2Integer value;
        status = FMI2GetInteger(m, &(vm.vr[0]), 1, &value);
        values[i] = value;
    }

    return status;
}

fmi3Status fmi3GetUInt64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt64 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetBoolean(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Boolean values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const fmi3ValueReference vr = valueReferences[i];

        const size_t j = vr - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;

        fmi2Boolean value = fmi2False;

        status = FMI2GetBoolean(m, &(vm.vr[0]), 1, &value);

        values[i] = value;
    }

    return status;
}

fmi3Status fmi3GetString(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3String values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetBinary(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    size_t valueSizes[],
    fmi3Binary values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetClock(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Clock values[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetFloat32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float32 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetFloat64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float64 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const size_t j = valueReferences[i] - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        status = FMI2SetReal(m, &(vm.vr[0]), 1, &values[i]);
    }

    return status;
}

fmi3Status fmi3SetInt8(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int8 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetUInt8(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt8 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetInt16(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int16 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetUInt16(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt16 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetInt32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const size_t j = valueReferences[i] - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        status = FMI2SetInteger(m, &(vm.vr[0]), 1, &values[i]);
    }

    return status;
}

fmi3Status fmi3SetUInt32(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt32 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetInt64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int64 values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const size_t j = valueReferences[i] - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;
        fmi2Integer value = (fmi2Integer)values[i];
        status = FMI2SetInteger(m, &(vm.vr[0]), 1, &value);
    }

    return status;
}

fmi3Status fmi3SetUInt64(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt64 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetBoolean(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Boolean values[],
    size_t nValues) {

    System* s = (System*)instance;

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < nValueReferences; i++) {

        const size_t j = valueReferences[i] - 1;

        if (j >= s->nVariables) {
            return FMIError;
        }

        VariableMapping vm = s->variables[j];
        FMIInstance* m = s->components[vm.ci[0]]->instance;

        const fmi2Boolean value = values[i];

        status = FMI2SetBoolean(m, &(vm.vr[0]), 1, &value);
    }

    return status;
}

fmi3Status fmi3SetString(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3String values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetBinary(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const size_t valueSizes[],
    const fmi3Binary values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetClock(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Clock values[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetNumberOfVariableDependencies(fmi3Instance instance,
    fmi3ValueReference valueReference,
    size_t* nDependencies) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetVariableDependencies(fmi3Instance instance,
    fmi3ValueReference dependent,
    size_t elementIndicesOfDependent[],
    fmi3ValueReference independents[],
    size_t elementIndicesOfIndependents[],
    fmi3DependencyKind dependencyKinds[],
    size_t nDependencies) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetFMUState(fmi3Instance instance, fmi3FMUState* FMUState) { NOT_IMPLEMENTED; }

fmi3Status fmi3SetFMUState(fmi3Instance instance, fmi3FMUState  FMUState) { NOT_IMPLEMENTED; }

fmi3Status fmi3FreeFMUState(fmi3Instance instance, fmi3FMUState* FMUState) { NOT_IMPLEMENTED; }

fmi3Status fmi3SerializedFMUStateSize(fmi3Instance instance,
    fmi3FMUState FMUState,
    size_t* size) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SerializeFMUState(fmi3Instance instance,
    fmi3FMUState FMUState,
    fmi3Byte serializedState[],
    size_t size) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3DeserializeFMUState(fmi3Instance instance,
    const fmi3Byte serializedState[],
    size_t size,
    fmi3FMUState* FMUState) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetDirectionalDerivative(fmi3Instance instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetAdjointDerivative(fmi3Instance instance,
    const fmi3ValueReference unknowns[],
    size_t nUnknowns,
    const fmi3ValueReference knowns[],
    size_t nKnowns,
    const fmi3Float64 seed[],
    size_t nSeed,
    fmi3Float64 sensitivity[],
    size_t nSensitivity) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3EnterConfigurationMode(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3ExitConfigurationMode(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3GetIntervalDecimal(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 intervals[],
    fmi3IntervalQualifier qualifiers[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetIntervalFraction(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt64 counters[],
    fmi3UInt64 resolutions[],
    fmi3IntervalQualifier qualifiers[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetShiftDecimal(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3Float64 shifts[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetShiftFraction(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    fmi3UInt64 counters[],
    fmi3UInt64 resolutions[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetIntervalDecimal(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float64 intervals[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetIntervalFraction(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt64 counters[],
    const fmi3UInt64 resolutions[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetShiftDecimal(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Float64 shifts[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetShiftFraction(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3UInt64 counters[],
    const fmi3UInt64 resolutions[]) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3EvaluateDiscreteStates(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3UpdateDiscreteStates(fmi3Instance instance,
    fmi3Boolean* discreteStatesNeedUpdate,
    fmi3Boolean* terminateSimulation,
    fmi3Boolean* nominalsOfContinuousStatesChanged,
    fmi3Boolean* valuesOfContinuousStatesChanged,
    fmi3Boolean* nextEventTimeDefined,
    fmi3Float64* nextEventTime) {
    NOT_IMPLEMENTED;
}

/***************************************************
Types for Functions for Model Exchange
****************************************************/

fmi3Status fmi3EnterContinuousTimeMode(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3CompletedIntegratorStep(fmi3Instance instance,
    fmi3Boolean  noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* enterEventMode,
    fmi3Boolean* terminateSimulation) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3SetTime(fmi3Instance instance, fmi3Float64 time) { NOT_IMPLEMENTED; }

fmi3Status fmi3SetContinuousStates(fmi3Instance instance,
    const fmi3Float64 continuousStates[],
    size_t nContinuousStates) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetContinuousStateDerivatives(fmi3Instance instance,
    fmi3Float64 derivatives[],
    size_t nContinuousStates) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetEventIndicators(fmi3Instance instance,
    fmi3Float64 eventIndicators[],
    size_t nEventIndicators) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetContinuousStates(fmi3Instance instance,
    fmi3Float64 continuousStates[],
    size_t nContinuousStates) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetNominalsOfContinuousStates(fmi3Instance instance,
    fmi3Float64 nominals[],
    size_t nContinuousStates) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetNumberOfEventIndicators(fmi3Instance instance,
    size_t* nEventIndicators) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3GetNumberOfContinuousStates(fmi3Instance instance,
    size_t* nContinuousStates) {
    NOT_IMPLEMENTED;
}

/***************************************************
Types for Functions for Co-Simulation
****************************************************/

fmi3Status fmi3EnterStepMode(fmi3Instance instance) { NOT_IMPLEMENTED; }

fmi3Status fmi3GetOutputDerivatives(fmi3Instance instance,
    const fmi3ValueReference valueReferences[],
    size_t nValueReferences,
    const fmi3Int32 orders[],
    fmi3Float64 values[],
    size_t nValues) {
    NOT_IMPLEMENTED;
}

fmi3Status fmi3DoStep(fmi3Instance instance,
    fmi3Float64 currentCommunicationPoint,
    fmi3Float64 communicationStepSize,
    fmi3Boolean noSetFMUStatePriorToCurrentPoint,
    fmi3Boolean* eventHandlingNeeded,
    fmi3Boolean* terminateSimulation,
    fmi3Boolean* earlyReturn,
    fmi3Float64* lastSuccessfulTime) {

    System* s = (System*)instance;

    s->time = currentCommunicationPoint + communicationStepSize;

    *eventHandlingNeeded = fmi3False;
    *terminateSimulation = fmi3False;
    *earlyReturn = fmi3False;
    *lastSuccessfulTime = s->time;

    return doStep(s, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint);
}

/***************************************************
Types for Functions for Scheduled Execution
****************************************************/

fmi3Status fmi3ActivateModelPartition(fmi3Instance instance,
    fmi3ValueReference clockReference,
    fmi3Float64 activationTime) {
    NOT_IMPLEMENTED;
}
