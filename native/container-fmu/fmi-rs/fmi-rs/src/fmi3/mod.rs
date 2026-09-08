#![allow(
    non_camel_case_types,
    non_snake_case,
    dead_code,
    clippy::too_many_arguments
)]

pub mod builder;
pub mod log;
pub mod types;

use crate::fmi3::log::Logger;
use crate::sim::SimulationError::{self};
use crate::{get_symbol, load_platform_binary};
use libloading::Library;
use std::ffi::{CStr, CString};
use std::os::raw::c_void;
use std::path::Path;
use std::ptr::{self, null, null_mut};
use std::sync::Arc;
use types::*;

#[cfg(all(target_arch = "aarch64", target_os = "linux"))]
pub const PLATFORM_TUPLE: &str = "aarch64-linux";

#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
pub const PLATFORM_TUPLE: &str = "x86_64-linux";

#[cfg(all(target_arch = "aarch64", target_os = "macos"))]
pub const PLATFORM_TUPLE: &str = "aarch64-darwin";

#[cfg(all(target_arch = "x86_64", target_os = "macos"))]
pub const PLATFORM_TUPLE: &str = "x86_64-darwin";

#[cfg(all(target_arch = "x86", target_os = "windows"))]
pub const PLATFORM_TUPLE: &str = "x86-windows";

#[cfg(all(target_arch = "x86_64", target_os = "windows"))]
pub const PLATFORM_TUPLE: &str = "x86_64-windows";

macro_rules! fmi_get {
    ($self:expr, $func:ident, $value_refs:expr, $values:expr) => {{
        debug_assert!($value_refs.len() <= $values.len());

        let status = unsafe {
            ($self.$func)(
                $self.instance,
                $value_refs.as_ptr(),
                $value_refs.len(),
                $values.as_mut_ptr(),
                $values.len(),
            )
        };

        let message = format!(
            "{}(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={}) -> {:?}",
            stringify!($func),
            $value_refs,
            $value_refs.len(),
            $values,
            $values.len(),
            status
        );

        if $self.logCalls {
            $self.log_call(status, &message);
        }

        status
    }};
}

macro_rules! fmi_set {
    ($self:expr, $func:ident, $value_refs:expr, $values:expr) => {{
        debug_assert!($value_refs.len() <= $values.len());

        let status = unsafe {
            ($self.$func)(
                $self.instance,
                $value_refs.as_ptr(),
                $value_refs.len(),
                $values.as_ptr(),
                $values.len(),
            )
        };

        let message = format!(
            "{}(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={}) -> {:?}",
            stringify!($func),
            $value_refs,
            $value_refs.len(),
            $values,
            $values.len(),
            status
        );

        if $self.logCalls {
            $self.log_call(status, &message);
        }

        status
    }};
}

impl Drop for FMU3 {
    fn drop(&mut self) {
        if !self.instance.is_null() {
            unsafe { (self.fmi3FreeInstance)(self.instance) };
            self.instance = null_mut();
            if self.logCalls {
                self.log_call(fmi3Status::Ok, "fmi3FreeInstance()");
            }
        }
    }
}

#[derive(Debug)]
pub struct Call {
    pub status: fmi3Status,
    pub message: String,
}

#[derive(Debug)]
pub struct Message {
    pub status: fmi3Status,
    pub category: String,
    pub message: String,
}

pub struct FMU3 {
    logger: Box<dyn Logger>,
    intermediateUpdateHandler: Option<Box<dyn IntermediateUpdateHandler>>,

    logCalls: bool,

    _lib: Box<Library>,

    fmi3GetVersion: fmi3GetVersionTYPE,
    fmi3SetDebugLogging: fmi3SetDebugLoggingTYPE,
    fmi3InstantiateModelExchange: fmi3InstantiateModelExchangeTYPE,
    fmi3InstantiateCoSimulation: fmi3InstantiateCoSimulationTYPE,
    fmi3InstantiateScheduledExecution: fmi3InstantiateScheduledExecutionTYPE,
    fmi3FreeInstance: fmi3FreeInstanceTYPE,
    fmi3EnterInitializationMode: fmi3EnterInitializationModeTYPE,
    fmi3ExitInitializationMode: fmi3ExitInitializationModeTYPE,
    fmi3EnterEventMode: fmi3EnterEventModeTYPE,
    fmi3Terminate: fmi3TerminateTYPE,
    fmi3Reset: fmi3ResetTYPE,
    fmi3GetFloat32: fmi3GetFloat32TYPE,
    fmi3GetFloat64: fmi3GetFloat64TYPE,
    fmi3GetInt8: fmi3GetInt8TYPE,
    fmi3GetUInt8: fmi3GetUInt8TYPE,
    fmi3GetInt16: fmi3GetInt16TYPE,
    fmi3GetUInt16: fmi3GetUInt16TYPE,
    fmi3GetInt32: fmi3GetInt32TYPE,
    fmi3GetUInt32: fmi3GetUInt32TYPE,
    fmi3GetInt64: fmi3GetInt64TYPE,
    fmi3GetUInt64: fmi3GetUInt64TYPE,
    fmi3GetBoolean: fmi3GetBooleanTYPE,
    fmi3GetString: fmi3GetStringTYPE,
    fmi3GetBinary: fmi3GetBinaryTYPE,
    fmi3GetClock: fmi3GetClockTYPE,
    fmi3SetFloat32: fmi3SetFloat32TYPE,
    fmi3SetFloat64: fmi3SetFloat64TYPE,
    fmi3SetInt8: fmi3SetInt8TYPE,
    fmi3SetUInt8: fmi3SetUInt8TYPE,
    fmi3SetInt16: fmi3SetInt16TYPE,
    fmi3SetUInt16: fmi3SetUInt16TYPE,
    fmi3SetInt32: fmi3SetInt32TYPE,
    fmi3SetUInt32: fmi3SetUInt32TYPE,
    fmi3SetInt64: fmi3SetInt64TYPE,
    fmi3SetUInt64: fmi3SetUInt64TYPE,
    fmi3SetBoolean: fmi3SetBooleanTYPE,
    fmi3SetString: fmi3SetStringTYPE,
    fmi3SetBinary: fmi3SetBinaryTYPE,
    fmi3SetClock: fmi3SetClockTYPE,
    fmi3GetNumberOfVariableDependencies: fmi3GetNumberOfVariableDependenciesTYPE,
    fmi3GetVariableDependencies: fmi3GetVariableDependenciesTYPE,
    fmi3GetFMUState: fmi3GetFMUStateTYPE,
    fmi3SetFMUState: fmi3SetFMUStateTYPE,
    fmi3FreeFMUState: fmi3FreeFMUStateTYPE,
    fmi3SerializedFMUStateSize: fmi3SerializedFMUStateSizeTYPE,
    fmi3SerializeFMUState: fmi3SerializeFMUStateTYPE,
    fmi3DeserializeFMUState: fmi3DeserializeFMUStateTYPE,
    fmi3GetDirectionalDerivative: fmi3GetDirectionalDerivativeTYPE,
    fmi3GetAdjointDerivative: fmi3GetAdjointDerivativeTYPE,
    fmi3EnterConfigurationMode: fmi3EnterConfigurationModeTYPE,
    fmi3ExitConfigurationMode: fmi3ExitConfigurationModeTYPE,
    fmi3GetIntervalDecimal: fmi3GetIntervalDecimalTYPE,
    fmi3GetIntervalFraction: fmi3GetIntervalFractionTYPE,
    fmi3GetShiftDecimal: fmi3GetShiftDecimalTYPE,
    fmi3GetShiftFraction: fmi3GetShiftFractionTYPE,
    fmi3SetIntervalDecimal: fmi3SetIntervalDecimalTYPE,
    fmi3SetIntervalFraction: fmi3SetIntervalFractionTYPE,
    fmi3SetShiftDecimal: fmi3SetShiftDecimalTYPE,
    fmi3SetShiftFraction: fmi3SetShiftFractionTYPE,
    fmi3EvaluateDiscreteStates: fmi3EvaluateDiscreteStatesTYPE,
    fmi3UpdateDiscreteStates: fmi3UpdateDiscreteStatesTYPE,
    fmi3EnterContinuousTimeMode: fmi3EnterContinuousTimeModeTYPE,
    fmi3CompletedIntegratorStep: fmi3CompletedIntegratorStepTYPE,
    fmi3SetTime: fmi3SetTimeTYPE,
    fmi3SetContinuousStates: fmi3SetContinuousStatesTYPE,
    fmi3GetContinuousStateDerivatives: fmi3GetContinuousStateDerivativesTYPE,
    fmi3GetEventIndicators: fmi3GetEventIndicatorsTYPE,
    fmi3GetContinuousStates: fmi3GetContinuousStatesTYPE,
    fmi3GetNominalsOfContinuousStates: fmi3GetNominalsOfContinuousStatesTYPE,
    fmi3GetNumberOfEventIndicators: fmi3GetNumberOfEventIndicatorsTYPE,
    fmi3GetNumberOfContinuousStates: fmi3GetNumberOfContinuousStatesTYPE,
    fmi3EnterStepMode: fmi3EnterStepModeTYPE,
    fmi3GetOutputDerivatives: fmi3GetOutputDerivativesTYPE,
    fmi3DoStep: fmi3DoStepTYPE,
    fmi3ActivateModelPartition: fmi3ActivateModelPartitionTYPE,

    instance: fmi3Instance,
}

#[unsafe(no_mangle)]
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub extern "C" fn logMessage(
    instanceEnvironment: fmi3InstanceEnvironment,
    status: fmi3Status,
    category: fmi3String,
    message: fmi3String,
) {
    let category_str = if !category.is_null() {
        unsafe { CStr::from_ptr(category).to_string_lossy().into_owned() }
    } else {
        "unknown".to_string()
    };

    let message_str = if !message.is_null() {
        unsafe { CStr::from_ptr(message).to_string_lossy().into_owned() }
    } else {
        "empty".to_string()
    };

    if !instanceEnvironment.is_null() {
        let fmu: &FMU3 = unsafe { &*(instanceEnvironment as *const FMU3) };
        fmu.logger.log_message(status, &category_str, &message_str);
    }
}

pub trait IntermediateUpdateHandler {
    fn required_intermediate_variables(&self) -> Vec<fmi3ValueReference>;
    fn intermediate_update(
        &self,
        fmu: &FMU3,
        intermediateUpdateTime: fmi3Float64,
        intermediateVariableSetRequested: fmi3Boolean,
        intermediateVariableGetAllowed: fmi3Boolean,
        intermediateStepFinished: fmi3Boolean,
        canReturnEarly: fmi3Boolean,
    ) -> (fmi3Boolean, fmi3Float64);
}

#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub extern "C" fn intermediateUpdate(
    instanceEnvironment: fmi3InstanceEnvironment,
    intermediateUpdateTime: fmi3Float64,
    intermediateVariableSetRequested: fmi3Boolean,
    intermediateVariableGetAllowed: fmi3Boolean,
    intermediateStepFinished: fmi3Boolean,
    canReturnEarly: fmi3Boolean,
    earlyReturnRequested: *mut fmi3Boolean,
    earlyReturnTime: *mut fmi3Float64,
) {
    if instanceEnvironment.is_null() {
        return;
    }

    let fmu: &FMU3 = unsafe { &*(instanceEnvironment as *const FMU3) };

    if let Some(handler) = &fmu.intermediateUpdateHandler {
        let (early_return_requested, early_return_time) = handler.intermediate_update(
            fmu,
            intermediateUpdateTime,
            intermediateVariableSetRequested,
            intermediateVariableGetAllowed,
            intermediateStepFinished,
            canReturnEarly,
        );

        if !earlyReturnRequested.is_null() {
            unsafe {
                *earlyReturnRequested = early_return_requested;
            }
        }

        if !earlyReturnTime.is_null() {
            unsafe {
                *earlyReturnTime = early_return_time;
            }
        }

        if fmu.logCalls {
            let message = format!(
                "fmi3IntermediateUpdateCallback(\
                intermediateUpdateTime={intermediateUpdateTime}, \
                intermediateVariableSetRequested={intermediateVariableSetRequested}, \
                intermediateVariableGetAllowed={intermediateVariableGetAllowed}, \
                intermediateStepFinished={intermediateStepFinished}, \
                canReturnEarly={canReturnEarly}, \
                earlyReturnRequested={early_return_requested}, \
                earlyReturnTime={early_return_time}\
            )"
            );
            fmu.logger.log_call(fmi3Status::Ok, &message);
        }
    }
}

impl FMU3 {
    fn new(
        unzipdir: &Path,
        modelIdentifier: &str,
        logger: Box<dyn Logger>,
        logCalls: bool,
        intermediateUpdateHandler: Option<Box<dyn IntermediateUpdateHandler>>,
    ) -> Result<FMU3, SimulationError> {
        let library = load_platform_binary(unzipdir, PLATFORM_TUPLE, modelIdentifier)?;

        /***************************************************
        Common Functions
        ****************************************************/

        let fmi3GetVersion = *get_symbol::<fmi3GetVersionTYPE>(&library, b"fmi3GetVersion")?;
        let fmi3SetDebugLogging =
            *get_symbol::<fmi3SetDebugLoggingTYPE>(&library, b"fmi3SetDebugLogging")?;
        let fmi3InstantiateModelExchange = *get_symbol::<fmi3InstantiateModelExchangeTYPE>(
            &library,
            b"fmi3InstantiateModelExchange",
        )?;
        let fmi3InstantiateCoSimulation = *get_symbol::<fmi3InstantiateCoSimulationTYPE>(
            &library,
            b"fmi3InstantiateCoSimulation",
        )?;
        let fmi3InstantiateScheduledExecution = *get_symbol::<fmi3InstantiateScheduledExecutionTYPE>(
            &library,
            b"fmi3InstantiateScheduledExecution",
        )?;
        let fmi3FreeInstance = *get_symbol::<fmi3FreeInstanceTYPE>(&library, b"fmi3FreeInstance")?;
        let fmi3EnterInitializationMode = *get_symbol::<fmi3EnterInitializationModeTYPE>(
            &library,
            b"fmi3EnterInitializationMode",
        )?;
        let fmi3ExitInitializationMode =
            *get_symbol::<fmi3ExitInitializationModeTYPE>(&library, b"fmi3ExitInitializationMode")?;
        let fmi3EnterEventMode =
            *get_symbol::<fmi3EnterEventModeTYPE>(&library, b"fmi3EnterEventMode")?;
        let fmi3Terminate = *get_symbol::<fmi3TerminateTYPE>(&library, b"fmi3Terminate")?;
        let fmi3Reset = *get_symbol::<fmi3ResetTYPE>(&library, b"fmi3Reset")?;
        let fmi3GetFloat32 = *get_symbol::<fmi3GetFloat32TYPE>(&library, b"fmi3GetFloat32")?;
        let fmi3GetFloat64 = *get_symbol::<fmi3GetFloat64TYPE>(&library, b"fmi3GetFloat64")?;
        let fmi3GetInt8 = *get_symbol::<fmi3GetInt8TYPE>(&library, b"fmi3GetInt8")?;
        let fmi3GetUInt8 = *get_symbol::<fmi3GetUInt8TYPE>(&library, b"fmi3GetUInt8")?;
        let fmi3GetInt16 = *get_symbol::<fmi3GetInt16TYPE>(&library, b"fmi3GetInt16")?;
        let fmi3GetUInt16 = *get_symbol::<fmi3GetUInt16TYPE>(&library, b"fmi3GetUInt16")?;
        let fmi3GetInt32 = *get_symbol::<fmi3GetInt32TYPE>(&library, b"fmi3GetInt32")?;
        let fmi3GetUInt32 = *get_symbol::<fmi3GetUInt32TYPE>(&library, b"fmi3GetUInt32")?;
        let fmi3GetInt64 = *get_symbol::<fmi3GetInt64TYPE>(&library, b"fmi3GetInt64")?;
        let fmi3GetUInt64 = *get_symbol::<fmi3GetUInt64TYPE>(&library, b"fmi3GetUInt64")?;
        let fmi3GetBoolean = *get_symbol::<fmi3GetBooleanTYPE>(&library, b"fmi3GetBoolean")?;
        let fmi3GetString = *get_symbol::<fmi3GetStringTYPE>(&library, b"fmi3GetString")?;
        let fmi3GetBinary = *get_symbol::<fmi3GetBinaryTYPE>(&library, b"fmi3GetBinary")?;
        let fmi3GetClock = *get_symbol::<fmi3GetClockTYPE>(&library, b"fmi3GetClock")?;
        let fmi3SetFloat32 = *get_symbol::<fmi3SetFloat32TYPE>(&library, b"fmi3SetFloat32")?;
        let fmi3SetFloat64 = *get_symbol::<fmi3SetFloat64TYPE>(&library, b"fmi3SetFloat64")?;
        let fmi3SetInt8 = *get_symbol::<fmi3SetInt8TYPE>(&library, b"fmi3SetInt8")?;
        let fmi3SetUInt8 = *get_symbol::<fmi3SetUInt8TYPE>(&library, b"fmi3SetUInt8")?;
        let fmi3SetInt16 = *get_symbol::<fmi3SetInt16TYPE>(&library, b"fmi3SetInt16")?;
        let fmi3SetUInt16 = *get_symbol::<fmi3SetUInt16TYPE>(&library, b"fmi3SetUInt16")?;
        let fmi3SetInt32 = *get_symbol::<fmi3SetInt32TYPE>(&library, b"fmi3SetInt32")?;
        let fmi3SetUInt32 = *get_symbol::<fmi3SetUInt32TYPE>(&library, b"fmi3SetUInt32")?;
        let fmi3SetInt64 = *get_symbol::<fmi3SetInt64TYPE>(&library, b"fmi3SetInt64")?;
        let fmi3SetUInt64 = *get_symbol::<fmi3SetUInt64TYPE>(&library, b"fmi3SetUInt64")?;
        let fmi3SetBoolean = *get_symbol::<fmi3SetBooleanTYPE>(&library, b"fmi3SetBoolean")?;
        let fmi3SetString = *get_symbol::<fmi3SetStringTYPE>(&library, b"fmi3SetString")?;
        let fmi3SetBinary = *get_symbol::<fmi3SetBinaryTYPE>(&library, b"fmi3SetBinary")?;
        let fmi3SetClock = *get_symbol::<fmi3SetClockTYPE>(&library, b"fmi3SetClock")?;
        let fmi3GetNumberOfVariableDependencies =
            *get_symbol::<fmi3GetNumberOfVariableDependenciesTYPE>(
                &library,
                b"fmi3GetNumberOfVariableDependencies",
            )?;
        let fmi3GetVariableDependencies = *get_symbol::<fmi3GetVariableDependenciesTYPE>(
            &library,
            b"fmi3GetVariableDependencies",
        )?;
        let fmi3GetFMUState = *get_symbol::<fmi3GetFMUStateTYPE>(&library, b"fmi3GetFMUState")?;
        let fmi3SetFMUState = *get_symbol::<fmi3SetFMUStateTYPE>(&library, b"fmi3SetFMUState")?;
        let fmi3FreeFMUState = *get_symbol::<fmi3FreeFMUStateTYPE>(&library, b"fmi3FreeFMUState")?;
        let fmi3SerializedFMUStateSize =
            *get_symbol::<fmi3SerializedFMUStateSizeTYPE>(&library, b"fmi3SerializedFMUStateSize")?;
        let fmi3SerializeFMUState =
            *get_symbol::<fmi3SerializeFMUStateTYPE>(&library, b"fmi3SerializeFMUState")?;
        let fmi3DeserializeFMUState =
            *get_symbol::<fmi3DeserializeFMUStateTYPE>(&library, b"fmi3DeserializeFMUState")?;
        let fmi3GetDirectionalDerivative = *get_symbol::<fmi3GetDirectionalDerivativeTYPE>(
            &library,
            b"fmi3GetDirectionalDerivative",
        )?;
        let fmi3GetAdjointDerivative =
            *get_symbol::<fmi3GetAdjointDerivativeTYPE>(&library, b"fmi3GetAdjointDerivative")?;
        let fmi3EnterConfigurationMode =
            *get_symbol::<fmi3EnterConfigurationModeTYPE>(&library, b"fmi3EnterConfigurationMode")?;
        let fmi3ExitConfigurationMode =
            *get_symbol::<fmi3ExitConfigurationModeTYPE>(&library, b"fmi3ExitConfigurationMode")?;
        let fmi3GetIntervalDecimal =
            *get_symbol::<fmi3GetIntervalDecimalTYPE>(&library, b"fmi3GetIntervalDecimal")?;
        let fmi3GetIntervalFraction =
            *get_symbol::<fmi3GetIntervalFractionTYPE>(&library, b"fmi3GetIntervalFraction")?;
        let fmi3GetShiftDecimal =
            *get_symbol::<fmi3GetShiftDecimalTYPE>(&library, b"fmi3GetShiftDecimal")?;
        let fmi3GetShiftFraction =
            *get_symbol::<fmi3GetShiftFractionTYPE>(&library, b"fmi3GetShiftFraction")?;
        let fmi3SetIntervalDecimal =
            *get_symbol::<fmi3SetIntervalDecimalTYPE>(&library, b"fmi3SetIntervalDecimal")?;
        let fmi3SetIntervalFraction =
            *get_symbol::<fmi3SetIntervalFractionTYPE>(&library, b"fmi3SetIntervalFraction")?;
        let fmi3SetShiftDecimal =
            *get_symbol::<fmi3SetShiftDecimalTYPE>(&library, b"fmi3SetShiftDecimal")?;
        let fmi3SetShiftFraction =
            *get_symbol::<fmi3SetShiftFractionTYPE>(&library, b"fmi3SetShiftFraction")?;
        let fmi3EvaluateDiscreteStates =
            *get_symbol::<fmi3EvaluateDiscreteStatesTYPE>(&library, b"fmi3EvaluateDiscreteStates")?;
        let fmi3UpdateDiscreteStates =
            *get_symbol::<fmi3UpdateDiscreteStatesTYPE>(&library, b"fmi3UpdateDiscreteStates")?;
        let fmi3EnterContinuousTimeMode = *get_symbol::<fmi3EnterContinuousTimeModeTYPE>(
            &library,
            b"fmi3EnterContinuousTimeMode",
        )?;
        let fmi3CompletedIntegratorStep = *get_symbol::<fmi3CompletedIntegratorStepTYPE>(
            &library,
            b"fmi3CompletedIntegratorStep",
        )?;
        let fmi3SetTime = *get_symbol::<fmi3SetTimeTYPE>(&library, b"fmi3SetTime")?;
        let fmi3SetContinuousStates =
            *get_symbol::<fmi3SetContinuousStatesTYPE>(&library, b"fmi3SetContinuousStates")?;
        let fmi3GetContinuousStateDerivatives = *get_symbol::<fmi3GetContinuousStateDerivativesTYPE>(
            &library,
            b"fmi3GetContinuousStateDerivatives",
        )?;
        let fmi3GetEventIndicators =
            *get_symbol::<fmi3GetEventIndicatorsTYPE>(&library, b"fmi3GetEventIndicators")?;
        let fmi3GetContinuousStates =
            *get_symbol::<fmi3GetContinuousStatesTYPE>(&library, b"fmi3GetContinuousStates")?;
        let fmi3GetNominalsOfContinuousStates = *get_symbol::<fmi3GetNominalsOfContinuousStatesTYPE>(
            &library,
            b"fmi3GetNominalsOfContinuousStates",
        )?;
        let fmi3GetNumberOfEventIndicators = *get_symbol::<fmi3GetNumberOfEventIndicatorsTYPE>(
            &library,
            b"fmi3GetNumberOfEventIndicators",
        )?;
        let fmi3GetNumberOfContinuousStates = *get_symbol::<fmi3GetNumberOfContinuousStatesTYPE>(
            &library,
            b"fmi3GetNumberOfContinuousStates",
        )?;
        let fmi3EnterStepMode =
            *get_symbol::<fmi3EnterStepModeTYPE>(&library, b"fmi3EnterStepMode")?;
        let fmi3GetOutputDerivatives =
            *get_symbol::<fmi3GetOutputDerivativesTYPE>(&library, b"fmi3GetOutputDerivatives")?;
        let fmi3DoStep = *get_symbol::<fmi3DoStepTYPE>(&library, b"fmi3DoStep")?;
        let fmi3ActivateModelPartition =
            *get_symbol::<fmi3ActivateModelPartitionTYPE>(&library, b"fmi3ActivateModelPartition")?;

        Ok(FMU3 {
            logger,
            intermediateUpdateHandler,
            logCalls,
            _lib: library,
            fmi3GetVersion,
            fmi3SetDebugLogging,
            fmi3InstantiateModelExchange,
            fmi3InstantiateCoSimulation,
            fmi3InstantiateScheduledExecution,
            fmi3FreeInstance,
            fmi3EnterInitializationMode,
            fmi3ExitInitializationMode,
            fmi3EnterEventMode,
            fmi3Terminate,
            fmi3Reset,
            fmi3GetFloat32,
            fmi3GetFloat64,
            fmi3GetInt8,
            fmi3GetUInt8,
            fmi3GetInt16,
            fmi3GetUInt16,
            fmi3GetInt32,
            fmi3GetUInt32,
            fmi3GetInt64,
            fmi3GetUInt64,
            fmi3GetBoolean,
            fmi3GetString,
            fmi3GetBinary,
            fmi3GetClock,
            fmi3SetFloat32,
            fmi3SetFloat64,
            fmi3SetInt8,
            fmi3SetUInt8,
            fmi3SetInt16,
            fmi3SetUInt16,
            fmi3SetInt32,
            fmi3SetUInt32,
            fmi3SetInt64,
            fmi3SetUInt64,
            fmi3SetBoolean,
            fmi3SetString,
            fmi3SetBinary,
            fmi3SetClock,
            fmi3GetNumberOfVariableDependencies,
            fmi3GetVariableDependencies,
            fmi3GetFMUState,
            fmi3SetFMUState,
            fmi3FreeFMUState,
            fmi3SerializedFMUStateSize,
            fmi3SerializeFMUState,
            fmi3DeserializeFMUState,
            fmi3GetDirectionalDerivative,
            fmi3GetAdjointDerivative,
            fmi3EnterConfigurationMode,
            fmi3ExitConfigurationMode,
            fmi3GetIntervalDecimal,
            fmi3GetIntervalFraction,
            fmi3GetShiftDecimal,
            fmi3GetShiftFraction,
            fmi3SetIntervalDecimal,
            fmi3SetIntervalFraction,
            fmi3SetShiftDecimal,
            fmi3SetShiftFraction,
            fmi3EvaluateDiscreteStates,
            fmi3UpdateDiscreteStates,
            fmi3EnterContinuousTimeMode,
            fmi3CompletedIntegratorStep,
            fmi3SetTime,
            fmi3SetContinuousStates,
            fmi3GetContinuousStateDerivatives,
            fmi3GetEventIndicators,
            fmi3GetContinuousStates,
            fmi3GetNominalsOfContinuousStates,
            fmi3GetNumberOfEventIndicators,
            fmi3GetNumberOfContinuousStates,
            fmi3EnterStepMode,
            fmi3GetOutputDerivatives,
            fmi3DoStep,
            fmi3ActivateModelPartition,
            instance: ptr::null_mut(),
        })
    }

    fn log_call(&self, status: fmi3Status, message: &str) {
        self.logger.log_call(status, message);
    }

    pub fn getVersion(&self) -> String {
        let version = unsafe {
            let version_cstr = (self.fmi3GetVersion)();
            CStr::from_ptr(version_cstr).to_string_lossy().into_owned()
        };
        if self.logCalls {
            let message = format!("fmi3GetVersion() -> \"{version}\"");
            self.log_call(fmi3Status::Ok, &message);
        }
        version
    }

    pub fn instantiateModelExchange(
        unzipdir: &Path,
        modelIdentifier: &str,
        instanceName: &str,
        instantiationToken: &str,
        visible: bool,
        loggingOn: bool,
        logger: Box<dyn Logger>,
        logCalls: bool,
    ) -> Result<Arc<FMU3>, SimulationError> {
        let fmu = Arc::new(FMU3::new(
            unzipdir,
            modelIdentifier,
            logger,
            logCalls,
            None,
        )?);

        let resource_path = unzipdir.join("resources").join("");

        let resourcePath = if resource_path.is_dir() {
            Some(resource_path.as_path())
        } else {
            None
        };

        let instance_name_cstr = CString::new(instanceName).unwrap();
        let instantiation_token_cstr = CString::new(instantiationToken).unwrap();
        let resource_path_cstr =
            resourcePath.and_then(|path| CString::new(path.to_string_lossy().as_ref()).ok());
        let path_ptr = resource_path_cstr
            .as_ref()
            .map(|cstr| cstr.as_ptr())
            .unwrap_or(ptr::null());
        let log_message = logMessage as *const fmi3LogMessageCallback;
        let instanceEnvironment = Arc::as_ptr(&fmu).cast::<c_void>() as *mut c_void;

        let instance = unsafe {
            (fmu.fmi3InstantiateModelExchange)(
                instance_name_cstr.as_ptr(),
                instantiation_token_cstr.as_ptr(),
                path_ptr,
                visible,
                loggingOn,
                instanceEnvironment,
                log_message,
            )
        };

        if fmu.logCalls {
            let status = if instance.is_null() {
                fmi3Status::Error
            } else {
                fmi3Status::Ok
            };

            let message = format!(
                "fmi3InstantiateModelExchange(instanceName=\"{}\", instantiationToken=\"{}\", resourcePath={:?}, visible={}, loggingOn={}, instanceEnvironment={:p}, logMessage={:p}) -> {:?}",
                instanceName,
                instantiationToken,
                resourcePath,
                visible,
                loggingOn,
                instanceEnvironment,
                log_message,
                instance
            );
            fmu.log_call(status, &message);
        }

        if instance.is_null() {
            Err(SimulationError::FMICall)
        } else {
            let fmu_ptr = instanceEnvironment as *mut FMU3;
            let mut_fmu: &mut FMU3 = unsafe { &mut *fmu_ptr };
            mut_fmu.instance = instance;
            Ok(fmu)
        }
    }

    pub fn instantiateCoSimulation(
        unzipdir: &Path,
        modelIdentifier: &str,
        instanceName: &str,
        instantiationToken: &str,
        visible: bool,
        loggingOn: bool,
        eventModeUsed: bool,
        earlyReturnAllowed: bool,
        logger: Box<dyn Logger>,
        logCalls: bool,
        intermediateUpdateHandler: Option<Box<dyn IntermediateUpdateHandler>>,
    ) -> Result<Arc<FMU3>, SimulationError> {
        let resource_path = unzipdir.join("resources").join("");

        let resourcePath = if resource_path.is_dir() {
            Some(resource_path.as_path())
        } else {
            None
        };

        let instance_name_cstr = CString::new(instanceName).unwrap();
        let instantiation_token_cstr = CString::new(instantiationToken).unwrap();
        let resource_path_cstr =
            resourcePath.and_then(|path| CString::new(path.to_string_lossy().as_ref()).ok());
        let path_ptr = resource_path_cstr
            .as_ref()
            .map(|cstr| cstr.as_ptr())
            .unwrap_or(ptr::null());
        let log_message = logMessage as *const fmi3LogMessageCallback;

        let (requiredIntermediateVariables, intermediate_update) =
            if let Some(handler) = intermediateUpdateHandler.as_ref() {
                (
                    handler.required_intermediate_variables(),
                    intermediateUpdate as *const fmi3IntermediateUpdateCallback,
                )
            } else {
                (
                    vec![],
                    ptr::null_mut() as *const fmi3IntermediateUpdateCallback,
                )
            };

        let fmu = Arc::new(FMU3::new(
            unzipdir,
            modelIdentifier,
            logger,
            logCalls,
            intermediateUpdateHandler,
        )?);

        let instanceEnvironment = Arc::as_ptr(&fmu).cast::<c_void>() as *mut c_void;

        let instance = unsafe {
            (fmu.fmi3InstantiateCoSimulation)(
                instance_name_cstr.as_ptr(),
                instantiation_token_cstr.as_ptr(),
                path_ptr,
                visible,
                loggingOn,
                eventModeUsed,
                earlyReturnAllowed,
                requiredIntermediateVariables.as_ptr(),
                requiredIntermediateVariables.len(),
                instanceEnvironment,
                log_message,
                intermediate_update,
            )
        };

        let status = if instance.is_null() {
            fmi3Status::Error
        } else {
            fmi3Status::Ok
        };

        if fmu.logCalls {
            let message = format!(
                "fmi3InstantiateCoSimulation(instanceName=\"{}\", instantiationToken=\"{}\", resourcePath={:?}, visible={}, loggingOn={}, eventModeUsed={}, earlyReturnAllowed={}, requiredIntermediateVariables={:?}, nRequiredIntermediateVariables={}, instanceEnvironment={:p}, logMessage={:p}, intermediateUpdate={:p}) -> {:p}",
                instanceName,
                instantiationToken,
                resourcePath,
                visible,
                loggingOn,
                eventModeUsed,
                earlyReturnAllowed,
                requiredIntermediateVariables,
                requiredIntermediateVariables.len(),
                instanceEnvironment,
                log_message,
                intermediate_update,
                instance
            );
            fmu.log_call(status, &message);
        }

        if instance.is_null() {
            Err(SimulationError::FMICall)
        } else {
            let fmu_ptr = instanceEnvironment as *mut FMU3;
            let mut_fmu: &mut FMU3 = unsafe { &mut *fmu_ptr };
            mut_fmu.instance = instance;
            Ok(fmu)
        }
    }

    pub fn terminate(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3Terminate)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3Termiate() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn enterInitializationMode(
        &self,
        tolerance: Option<fmi3Float64>,
        startTime: fmi3Float64,
        stopTime: Option<fmi3Float64>,
    ) -> fmi3Status {
        let (toleranceDefined, tolerance) = if let Some(tolerance) = tolerance {
            (true, tolerance)
        } else {
            (false, 0.0)
        };

        let (stopTimeDefined, stopTime) = if let Some(stopTime) = stopTime {
            (true, stopTime)
        } else {
            (false, 0.0)
        };

        let status = unsafe {
            (self.fmi3EnterInitializationMode)(
                self.instance,    // instance
                toleranceDefined, // toleranceDefined
                tolerance,        // tolerance
                startTime,        // startTime
                stopTimeDefined,  // stopTimeDefined
                stopTime,         // stopTime
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3EnterInitializationMode(toleranceDefined={toleranceDefined}, tolerance={tolerance}, startTime={startTime}, stopTimeDefined={stopTimeDefined}, stopTime={stopTime}) -> {status:?}",
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn exitInitializationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3ExitInitializationMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3ExitInitializationMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn reset(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3Reset)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3Reset() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn doStep(
        &self,
        currentCommunicationPoint: fmi3Float64,
        communicationStepSize: fmi3Float64,
        noSetFMUStatePriorToCurrentPoint: fmi3Boolean,
        eventHandlingNeeded: &mut fmi3Boolean,
        terminateSimulation: &mut fmi3Boolean,
        earlyReturn: &mut fmi3Boolean,
        lastSuccessfulTime: &mut fmi3Float64,
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3DoStep)(
                self.instance,
                currentCommunicationPoint,
                communicationStepSize,
                noSetFMUStatePriorToCurrentPoint,
                eventHandlingNeeded,
                terminateSimulation,
                earlyReturn,
                lastSuccessfulTime,
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3DoStep(currentCommunicationPoint={}, communicationStepSize={}, noSetFMUStatePriorToCurrentPoint={}, eventHandlingNeeded={:?}, terminateSimulation={:?}, earlyReturn={:?}, lastSuccessfulTime={:?}) -> {:?}",
                currentCommunicationPoint,
                communicationStepSize,
                noSetFMUStatePriorToCurrentPoint,
                eventHandlingNeeded,
                terminateSimulation,
                earlyReturn,
                lastSuccessfulTime,
                status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn getFloat32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Float32],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetFloat32, valueReferences, values)
    }

    pub fn getFloat64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Float64],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetFloat64, valueReferences, values)
    }

    pub fn getInt8(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Int8],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetInt8, valueReferences, values)
    }

    pub fn getUInt8(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3UInt8],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetUInt8, valueReferences, values)
    }

    pub fn getInt16(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Int16],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetInt16, valueReferences, values)
    }

    pub fn getUInt16(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3UInt16],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetUInt16, valueReferences, values)
    }

    pub fn getInt32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Int32],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetInt32, valueReferences, values)
    }

    pub fn getUInt32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3UInt32],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetUInt32, valueReferences, values)
    }

    pub fn getInt64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Int64],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetInt64, valueReferences, values)
    }

    pub fn getUInt64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3UInt64],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetUInt64, valueReferences, values)
    }

    pub fn getBoolean(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Boolean],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetBoolean, valueReferences, values)
    }

    pub fn getString(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [String],
    ) -> fmi3Status {
        debug_assert!(valueReferences.len() <= values.len());

        let mut buffer: Vec<fmi3String> = vec![null(); values.len()];

        let status = unsafe {
            (self.fmi3GetString)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                buffer.as_mut_ptr(),
                buffer.len(),
            )
        };

        for (i, v) in buffer.iter().enumerate() {
            values[i] = unsafe { CStr::from_ptr(*v).to_string_lossy().into_owned() };
        }

        if self.logCalls {
            let message = format!(
                "fmi3GetString(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                values,
                values.len(),
                status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn getClock(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [fmi3Clock],
    ) -> fmi3Status {
        fmi_get!(self, fmi3GetClock, valueReferences, values)
    }

    pub fn getBinary(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &mut [Vec<fmi3Byte>],
    ) -> fmi3Status {
        let mut sizes: Vec<usize> = vec![0; values.len()];
        let mut value_ptrs = vec![null(); values.len()];

        let status = unsafe {
            (self.fmi3GetBinary)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                sizes.as_mut_ptr(),
                value_ptrs.as_mut_ptr(),
                values.len(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3GetBinary(valueReferences={:?}, nValueReferences={}, sizes={:?}, values={:?}, nValues={}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                sizes,
                value_ptrs,
                value_ptrs.len(),
                status,
            );
            self.log_call(status, &message);
        }

        for (i, (&ptr, size)) in value_ptrs.iter().zip(sizes.iter()).enumerate() {
            if !ptr.is_null() && *size > 0 {
                let slice = unsafe { std::slice::from_raw_parts(ptr as *const fmi3Byte, *size) };
                values[i] = slice.to_vec();
            } else {
                values[i] = Vec::new();
            }
        }

        status
    }

    pub fn setFloat32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Float32],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetFloat32, valueReferences, values)
    }

    pub fn setFloat64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Float64],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetFloat64, valueReferences, values)
    }

    pub fn setInt8(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Int8],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetInt8, valueReferences, values)
    }

    pub fn setUInt8(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3UInt8],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetUInt8, valueReferences, values)
    }

    pub fn setInt16(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Int16],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetInt16, valueReferences, values)
    }

    pub fn setUInt16(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3UInt16],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetUInt16, valueReferences, values)
    }

    pub fn setInt32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Int32],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetInt32, valueReferences, values)
    }

    pub fn setUInt32(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3UInt32],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetUInt32, valueReferences, values)
    }

    pub fn setInt64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Int64],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetInt64, valueReferences, values)
    }

    pub fn setUInt64(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3UInt64],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetUInt64, valueReferences, values)
    }

    pub fn setBoolean(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Boolean],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetBoolean, valueReferences, values)
    }

    pub fn setString(&self, valueReferences: &[fmi3ValueReference], values: &[&str]) -> fmi3Status {
        debug_assert!(valueReferences.len() <= values.len());

        let values: Vec<CString> = values.iter().map(|&v| CString::new(v).unwrap()).collect();

        let values2: Vec<fmi3String> = values.iter().map(|v| v.as_ptr() as fmi3String).collect();

        let status = unsafe {
            (self.fmi3SetString)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                values2.as_ptr(),
                values2.len(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3SetString(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                values,
                values.len(),
                status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn setClock(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[fmi3Clock],
    ) -> fmi3Status {
        fmi_set!(self, fmi3SetClock, valueReferences, values)
    }

    pub fn setBinary(
        &self,
        valueReferences: &[fmi3ValueReference],
        values: &[&[fmi3Byte]],
    ) -> fmi3Status {
        let sizes: Vec<usize> = values.iter().map(|v| v.len()).collect();
        let value_ptrs: Vec<fmi3Binary> = values.iter().map(|v| v.as_ptr()).collect();

        let status = unsafe {
            (self.fmi3SetBinary)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                sizes.as_ptr(),
                value_ptrs.as_ptr(),
                value_ptrs.len(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3SetBinary(valueReferences={:?}, nValueReferences={}, sizes={:?}, values={:?}, nValues={}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                sizes,
                value_ptrs,
                value_ptrs.len(),
                status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn setDebugLogging(&self, loggingOn: fmi3Boolean, categories: &[fmi3String]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SetDebugLogging)(
                self.instance,
                loggingOn,
                categories.len(),
                categories.as_ptr(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3SetDebugLogging(loggingOn={}, nCategories={}) -> {:?}",
                loggingOn,
                categories.len(),
                status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn enterEventMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterEventMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3EnterEventMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn enterStepMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterStepMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3EnterStepMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn getNumberOfVariableDependencies(
        &self,
        valueReference: fmi3ValueReference,
    ) -> Result<usize, fmi3Status> {
        let mut nDependencies: usize = 0;

        let status = unsafe {
            (self.fmi3GetNumberOfVariableDependencies)(
                self.instance,
                valueReference,
                &mut nDependencies,
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3GetNumberOfVariableDependencies(valueReference={}, nDependencies={}) -> {:?}",
                valueReference, nDependencies, status
            );
            self.log_call(status, &message);
        }

        if status == fmi3Status::Ok {
            Ok(nDependencies)
        } else {
            Err(status)
        }
    }

    pub fn getVariableDependencies(
        &self,
        valueReference: fmi3ValueReference,
        elementIndicesOfDependent: &mut [usize],
        independentVariables: &mut [fmi3ValueReference],
        elementIndicesOfIndependents: &mut [usize],
        dependencyKinds: &mut [fmi3DependencyKind],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetVariableDependencies)(
                self.instance,
                valueReference,
                elementIndicesOfDependent.as_mut_ptr(),
                independentVariables.as_mut_ptr(),
                elementIndicesOfIndependents.as_mut_ptr(),
                dependencyKinds.as_mut_ptr(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3GetVariableDependencies(valueReference={}) -> {:?}",
                valueReference, status,
            );
            self.log_call(status, &message);
        }

        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn getFMUState(&self, FMUState: &mut fmi3FMUState) -> fmi3Status {
        let status = unsafe { (self.fmi3GetFMUState)(self.instance, FMUState) };
        if self.logCalls {
            let message = format!("fmi3GetFMUState(FMUState={FMUState:p}) -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn setFMUState(&self, FMUState: fmi3FMUState) -> fmi3Status {
        let status = unsafe { (self.fmi3SetFMUState)(self.instance, FMUState) };
        if self.logCalls {
            let message = format!("fmi3SetFMUState(FMUState={FMUState:p}) -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn freeFMUState(&self, FMUState: &mut fmi3FMUState) -> fmi3Status {
        let status = unsafe { (self.fmi3FreeFMUState)(self.instance, FMUState) };
        if self.logCalls {
            let message = format!("fmi3FreeFMUState(FMUState={FMUState:p}) -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn serializedFMUStateSize(&self, FMUState: fmi3FMUState, size: &mut usize) -> fmi3Status {
        let status = unsafe { (self.fmi3SerializedFMUStateSize)(self.instance, FMUState, size) };
        if self.logCalls {
            let message = format!(
                "fmi3SerializedFMUStateSize(FMUState={:p}, size={}) -> {:?}",
                FMUState, size, status
            );
            self.log_call(status, &message);
        }
        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn serializeFMUState(
        &self,
        fmuState: fmi3FMUState,
        serializedState: &mut [fmi3Byte],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SerializeFMUState)(
                self.instance,
                fmuState,
                serializedState.as_mut_ptr(),
                serializedState.len(),
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3SerializeFMUState(size={}) -> {status:?}",
                serializedState.len()
            );
            self.log_call(status, &message);
        }
        status
    }

    #[allow(clippy::not_unsafe_ptr_arg_deref)]
    pub fn deserializeFMUState(
        &self,
        serializedState: &[fmi3Byte],
        FMUState: &mut fmi3FMUState,
    ) -> fmi3Status {
        let size = serializedState.len();
        let serializedState = serializedState.as_ptr();

        let status = unsafe {
            (self.fmi3DeserializeFMUState)(self.instance, serializedState, size, FMUState)
        };

        if self.logCalls {
            let message = format!(
                "fmi3DeserializeFMUState(serializedState={serializedState:p}, size={size}, FMUState={FMUState:p}) -> {status:?}"
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn getDirectionalDerivative(
        &self,
        unknowns: &[fmi3ValueReference],
        knowns: &[fmi3ValueReference],
        seed: &[fmi3Float64],
        sensitivity: &mut [fmi3Float64],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetDirectionalDerivative)(
                self.instance,
                unknowns.as_ptr(),
                unknowns.len(),
                knowns.as_ptr(),
                knowns.len(),
                seed.as_ptr(),
                seed.len(),
                sensitivity.as_mut_ptr(),
                sensitivity.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetDirectionalDerivative(unknowns: {:?}, nUnknowns: {}, knowns: {:?}, nKnowns: {}, seed: {:?}, nSeed: {}, sensitivity: {:?}, nSensitivity: {}) -> {:?}",
                unknowns,
                unknowns.len(),
                knowns,
                knowns.len(),
                seed,
                seed.len(),
                sensitivity,
                sensitivity.len(),
                status,
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getAdjointDerivative(
        &self,
        unknowns: &[fmi3ValueReference],
        knowns: &[fmi3ValueReference],
        seed: &[fmi3Float64],
        sensitivity: &mut [fmi3Float64],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetAdjointDerivative)(
                self.instance,
                unknowns.as_ptr(),
                unknowns.len(),
                knowns.as_ptr(),
                knowns.len(),
                seed.as_ptr(),
                seed.len(),
                sensitivity.as_mut_ptr(),
                sensitivity.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetAdjointDerivative(unknowns={:?}, nUnknowns={}, knowns={:?}, nKnowns={}, seed={:?}, nSeed={}, sensitivity={:?}, nSensitivity={}) -> {status:?}",
                unknowns,
                unknowns.len(),
                knowns,
                knowns.len(),
                seed,
                seed.len(),
                sensitivity,
                sensitivity.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn enterConfigurationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterConfigurationMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3EnterConfigurationMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn exitConfigurationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3ExitConfigurationMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3ExitConfigurationMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn getIntervalDecimal(
        &self,
        valueReferences: &[fmi3ValueReference],
        intervals: &mut [fmi3Float64],
        qualifiers: &mut [fmi3IntervalQualifier],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetIntervalDecimal)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                intervals.as_mut_ptr(),
                qualifiers.as_mut_ptr(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetIntervalDecimal(valueReferences={:?}, ValueReferences={}, intervals={:?}, qualifiers={:?}) -> {status:?}",
                valueReferences,
                valueReferences.len(),
                intervals,
                qualifiers,
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getIntervalFraction(
        &self,
        valueReferences: &[fmi3ValueReference],
        counters: &mut [fmi3UInt64],
        resolutions: &mut [fmi3UInt64],
        qualifiers: &mut [fmi3IntervalQualifier],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetIntervalFraction)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                counters.as_mut_ptr(),
                resolutions.as_mut_ptr(),
                qualifiers.as_mut_ptr(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetIntervalFraction(valueReferences={:?}, ValueReferences={}, counters={:?}, resolutions={:?}, qualifiers={:?}) -> {status:?}",
                valueReferences,
                valueReferences.len(),
                counters,
                resolutions,
                qualifiers,
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn setIntervalDecimal(
        &self,
        valueReferences: &[fmi3ValueReference],
        intervals: &[fmi3Float64],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SetIntervalDecimal)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                intervals.as_ptr(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3SetIntervalDecimal(valueReferences={:?}, nValueReferences={}, intervals={:?}) -> {status:?}",
                valueReferences,
                valueReferences.len(),
                intervals,
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn setIntervalFraction(
        &self,
        valueReferences: &[fmi3ValueReference],
        counters: &[fmi3UInt64],
        resolutions: &[fmi3UInt64],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SetIntervalFraction)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                counters.as_ptr(),
                resolutions.as_ptr(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3SetIntervalFraction(valueReferences={:?}, nValueReferences={}, counters={:?}, resolutions={:?}) -> {status:?}",
                valueReferences,
                valueReferences.len(),
                counters,
                resolutions,
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn enterContinuousTimeMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterContinuousTimeMode)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3EnterContinuousTimeMode() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn completedIntegratorStep(
        &self,
        noSetFMUStatePriorToCurrentPoint: fmi3Boolean,
        enterEventMode: &mut fmi3Boolean,
        terminateSimulation: &mut fmi3Boolean,
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3CompletedIntegratorStep)(
                self.instance,
                noSetFMUStatePriorToCurrentPoint,
                enterEventMode,
                terminateSimulation,
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3CompletedIntegratorStep(noSetFMUStatePriorToCurrentPoint={}, enterEventMode={}, terminateSimulation={}) -> {:?}",
                noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation, status,
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn setTime(&self, time: fmi3Float64) -> fmi3Status {
        let status = unsafe { (self.fmi3SetTime)(self.instance, time) };
        if self.logCalls {
            let message = format!("fmi3SetTime(time={time}) -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn setContinuousStates(&self, continuousStates: &[fmi3Float64]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SetContinuousStates)(
                self.instance,
                continuousStates.as_ptr(),
                continuousStates.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3SetContinuousStates(continuousStates={:?}, nContinuousStates={}) -> {status:?}",
                continuousStates,
                continuousStates.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getContinuousStates(&self, continuousStates: &mut [fmi3Float64]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetContinuousStates)(
                self.instance,
                continuousStates.as_mut_ptr(),
                continuousStates.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetContinuousStates(continuousStates={:?}, nContinuousStates={}) -> {status:?}",
                continuousStates,
                continuousStates.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getContinuousStateDerivatives(&self, derivatives: &mut [fmi3Float64]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetContinuousStateDerivatives)(
                self.instance,
                derivatives.as_mut_ptr(),
                derivatives.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetContinuousStateDerivatives(derivatives={:?}, nDerivatives={}) -> {status:?}",
                derivatives,
                derivatives.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getEventIndicators(&self, eventIndicators: &mut [fmi3Float64]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetEventIndicators)(
                self.instance,
                eventIndicators.as_mut_ptr(),
                eventIndicators.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetEventIndicators(eventIndicators={:?}, nEventIndicators={}) -> {status:?}",
                eventIndicators,
                eventIndicators.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getNominalsOfContinuousStates(&self, nominals: &mut [fmi3Float64]) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetNominalsOfContinuousStates)(
                self.instance,
                nominals.as_mut_ptr(),
                nominals.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetNominalsOfContinuousStates(nominals={:?}, nNominals={}) -> {status:?}",
                nominals,
                nominals.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn getNumberOfEventIndicators(&self, nEventIndicators: &mut usize) -> fmi3Status {
        let status =
            unsafe { (self.fmi3GetNumberOfEventIndicators)(self.instance, nEventIndicators) };

        if self.logCalls {
            let message = format!(
                "fmi3GetNumberOfEventIndicators(nEventIndicators={nEventIndicators}) -> {status:?}"
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn getNumberOfContinuousStates(&self, nContinuousStates: &mut usize) -> fmi3Status {
        let status =
            unsafe { (self.fmi3GetNumberOfContinuousStates)(self.instance, nContinuousStates) };

        if self.logCalls {
            let message = format!(
                "fmi3GetNumberOfContinuousStates(nContinuousStates={nContinuousStates}) -> {status:?}"
            );
            self.log_call(status, &message);
        }

        status
    }

    pub fn evaluateDiscreteStates(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EvaluateDiscreteStates)(self.instance) };
        if self.logCalls {
            let message = format!("fmi3EvaluateDiscreteStates() -> {status:?}");
            self.log_call(status, &message);
        }
        status
    }

    pub fn updateDiscreteStates(
        &self,
        discreteStatesNeedUpdate: &mut fmi3Boolean,
        terminateSimulation: &mut fmi3Boolean,
        nominalsOfContinuousStatesChanged: &mut fmi3Boolean,
        valuesOfContinuousStatesChanged: &mut fmi3Boolean,
        nextEventTime: &mut Option<fmi3Float64>,
    ) -> fmi3Status {
        let mut nextEventTimeDefined = false;
        let mut nextEventTimeValue = 0.0;

        let status = unsafe {
            (self.fmi3UpdateDiscreteStates)(
                self.instance,
                discreteStatesNeedUpdate,
                terminateSimulation,
                nominalsOfContinuousStatesChanged,
                valuesOfContinuousStatesChanged,
                &mut nextEventTimeDefined,
                &mut nextEventTimeValue,
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3UpdateDiscreteStates(discreteStatesNeedUpdate={discreteStatesNeedUpdate}, terminateSimulation={terminateSimulation}, nominalsOfContinuousStatesChanged={nominalsOfContinuousStatesChanged}, valuesOfContinuousStatesChanged={valuesOfContinuousStatesChanged}, nextEventTimeDefined={nextEventTimeDefined}, nextEventTime={nextEventTimeValue}) -> {status:?}"
            );
            self.log_call(status, &message);
        }

        if nextEventTimeDefined {
            *nextEventTime = Some(nextEventTimeValue);
        } else {
            *nextEventTime = None;
        }

        status
    }

    pub fn getOutputDerivatives(
        &self,
        valueReferences: &[fmi3ValueReference],
        orders: &[fmi3Int32],
        values: &mut [fmi3Float64],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetOutputDerivatives)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                orders.as_ptr(),
                values.as_mut_ptr(),
                values.len(),
            )
        };
        if self.logCalls {
            let message = format!(
                "fmi3GetOutputDerivatives(valueReferences={:?}, nValueReferences={}, orders={:?}, values={:?}, nValues={}) -> {status:?}",
                valueReferences,
                valueReferences.len(),
                orders,
                values,
                values.len(),
            );
            self.log_call(status, &message);
        }
        status
    }

    pub fn activateModelPartition(
        &self,
        clockReference: fmi3ValueReference,
        activationTime: fmi3Float64,
        priority: fmi3Float64,
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3ActivateModelPartition)(
                self.instance,
                clockReference,
                activationTime,
                priority,
            )
        };

        if self.logCalls {
            let message = format!(
                "fmi3ActivateModelPartition(clockReference={}, activationTime={}, priority={}) -> {:?}",
                clockReference, activationTime, priority, status
            );
            self.log_call(status, &message);
        }

        status
    }
}
