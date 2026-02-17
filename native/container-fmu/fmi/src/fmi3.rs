#![allow(non_camel_case_types, non_snake_case, dead_code)]

pub mod types;

use crate::{SHARED_LIBRARY_EXTENSION, types::*};
use libloading::{Library, Symbol};
use std::error::Error;
use std::ffi::{CStr, CString};
use std::os::raw::{c_uint, c_void};
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

/// Macro to check FMI status and return early if error or fatal
/// Usage: fmi_check_status!(status);
#[macro_export]
macro_rules! fmi_check_status {
    ($status:expr) => {{
        let __fmi_status = $status;
        if __fmi_status > fmi3Warning {
            return __fmi_status;
        }
    }};
}

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
            "{}(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={})",
            stringify!($func),
            $value_refs,
            $value_refs.len(),
            $values,
            $values.len()
        );

        if let Some(cb) = &$self.logFMICall {
            cb(&status, &message);
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
            "{}(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={})",
            stringify!($func),
            $value_refs,
            $value_refs.len(),
            $values,
            $values.len()
        );

        if let Some(cb) = &$self.logFMICall {
            cb(&status, &message);
        }

        status
    }};
}

impl Drop for FMU3 {
    fn drop(&mut self) {
        if !self.instance.is_null() {
            unsafe { (self.fmi3FreeInstance)(self.instance) };
            self.instance = null_mut();
            if let Some(cb) = &self.logFMICall {
                cb(&fmi3OK, "fmi3FreeInstance()");
            }
        }
    }
}

pub struct FMU3 {
    
    logFMICall: Option<Arc<LogFMICallCallback>>,
    logMessage: Option<Arc<LogMessageCallback>>,
    
    _lib: Box<Library>,

    fmi3GetVersion: Symbol<'static, fmi3GetVersionTYPE>,
    fmi3SetDebugLogging: Symbol<'static, fmi3SetDebugLoggingTYPE>,
    fmi3InstantiateModelExchange: Symbol<'static, fmi3InstantiateModelExchangeTYPE>,
    fmi3InstantiateCoSimulation: Symbol<'static, fmi3InstantiateCoSimulationTYPE>,
    fmi3InstantiateScheduledExecution: Symbol<'static, fmi3InstantiateScheduledExecutionTYPE>,
    fmi3FreeInstance: Symbol<'static, fmi3FreeInstanceTYPE>,
    fmi3EnterInitializationMode: Symbol<'static, fmi3EnterInitializationModeTYPE>,
    fmi3ExitInitializationMode: Symbol<'static, fmi3ExitInitializationModeTYPE>,
    fmi3EnterEventMode: Symbol<'static, fmi3EnterEventModeTYPE>,
    fmi3Terminate: Symbol<'static, fmi3TerminateTYPE>,
    fmi3Reset: Symbol<'static, fmi3ResetTYPE>,
    fmi3GetFloat32: Symbol<'static, fmi3GetFloat32TYPE>,
    fmi3GetFloat64: Symbol<'static, fmi3GetFloat64TYPE>,
    fmi3GetInt8: Symbol<'static, fmi3GetInt8TYPE>,
    fmi3GetUInt8: Symbol<'static, fmi3GetUInt8TYPE>,
    fmi3GetInt16: Symbol<'static, fmi3GetInt16TYPE>,
    fmi3GetUInt16: Symbol<'static, fmi3GetUInt16TYPE>,
    fmi3GetInt32: Symbol<'static, fmi3GetInt32TYPE>,
    fmi3GetUInt32: Symbol<'static, fmi3GetUInt32TYPE>,
    fmi3GetInt64: Symbol<'static, fmi3GetInt64TYPE>,
    fmi3GetUInt64: Symbol<'static, fmi3GetUInt64TYPE>,
    fmi3GetBoolean: Symbol<'static, fmi3GetBooleanTYPE>,
    fmi3GetString: Symbol<'static, fmi3GetStringTYPE>,
    fmi3GetBinary: Symbol<'static, fmi3GetBinaryTYPE>,
    fmi3GetClock: Symbol<'static, fmi3GetClockTYPE>,
    fmi3SetFloat32: Symbol<'static, fmi3SetFloat32TYPE>,
    fmi3SetFloat64: Symbol<'static, fmi3SetFloat64TYPE>,
    fmi3SetInt8: Symbol<'static, fmi3SetInt8TYPE>,
    fmi3SetUInt8: Symbol<'static, fmi3SetUInt8TYPE>,
    fmi3SetInt16: Symbol<'static, fmi3SetInt16TYPE>,
    fmi3SetUInt16: Symbol<'static, fmi3SetUInt16TYPE>,
    fmi3SetInt32: Symbol<'static, fmi3SetInt32TYPE>,
    fmi3SetUInt32: Symbol<'static, fmi3SetUInt32TYPE>,
    fmi3SetInt64: Symbol<'static, fmi3SetInt64TYPE>,
    fmi3SetUInt64: Symbol<'static, fmi3SetUInt64TYPE>,
    fmi3SetBoolean: Symbol<'static, fmi3SetBooleanTYPE>,
    fmi3SetString: Symbol<'static, fmi3SetStringTYPE>,
    fmi3SetBinary: Symbol<'static, fmi3SetBinaryTYPE>,
    fmi3SetClock: Symbol<'static, fmi3SetClockTYPE>,
    fmi3GetNumberOfVariableDependencies: Symbol<'static, fmi3GetNumberOfVariableDependenciesTYPE>,
    fmi3GetVariableDependencies: Symbol<'static, fmi3GetVariableDependenciesTYPE>,
    fmi3GetFMUState: Symbol<'static, fmi3GetFMUStateTYPE>,
    fmi3SetFMUState: Symbol<'static, fmi3SetFMUStateTYPE>,
    fmi3FreeFMUState: Symbol<'static, fmi3FreeFMUStateTYPE>,
    fmi3SerializedFMUStateSize: Symbol<'static, fmi3SerializedFMUStateSizeTYPE>,
    fmi3SerializeFMUState: Symbol<'static, fmi3SerializeFMUStateTYPE>,
    fmi3DeserializeFMUState: Symbol<'static, fmi3DeserializeFMUStateTYPE>,
    fmi3GetDirectionalDerivative: Symbol<'static, fmi3GetDirectionalDerivativeTYPE>,
    fmi3GetAdjointDerivative: Symbol<'static, fmi3GetAdjointDerivativeTYPE>,
    fmi3EnterConfigurationMode: Symbol<'static, fmi3EnterConfigurationModeTYPE>,
    fmi3ExitConfigurationMode: Symbol<'static, fmi3ExitConfigurationModeTYPE>,
    fmi3GetIntervalDecimal: Symbol<'static, fmi3GetIntervalDecimalTYPE>,
    fmi3GetIntervalFraction: Symbol<'static, fmi3GetIntervalFractionTYPE>,
    fmi3GetShiftDecimal: Symbol<'static, fmi3GetShiftDecimalTYPE>,
    fmi3GetShiftFraction: Symbol<'static, fmi3GetShiftFractionTYPE>,
    fmi3SetIntervalDecimal: Symbol<'static, fmi3SetIntervalDecimalTYPE>,
    fmi3SetIntervalFraction: Symbol<'static, fmi3SetIntervalFractionTYPE>,
    fmi3SetShiftDecimal: Symbol<'static, fmi3SetShiftDecimalTYPE>,
    fmi3SetShiftFraction: Symbol<'static, fmi3SetShiftFractionTYPE>,
    fmi3EvaluateDiscreteStates: Symbol<'static, fmi3EvaluateDiscreteStatesTYPE>,
    fmi3UpdateDiscreteStates: Symbol<'static, fmi3UpdateDiscreteStatesTYPE>,
    fmi3EnterContinuousTimeMode: Symbol<'static, fmi3EnterContinuousTimeModeTYPE>,
    fmi3CompletedIntegratorStep: Symbol<'static, fmi3CompletedIntegratorStepTYPE>,
    fmi3SetTime: Symbol<'static, fmi3SetTimeTYPE>,
    fmi3SetContinuousStates: Symbol<'static, fmi3SetContinuousStatesTYPE>,
    fmi3GetContinuousStateDerivatives: Symbol<'static, fmi3GetContinuousStateDerivativesTYPE>,
    fmi3GetEventIndicators: Symbol<'static, fmi3GetEventIndicatorsTYPE>,
    fmi3GetContinuousStates: Symbol<'static, fmi3GetContinuousStatesTYPE>,
    fmi3GetNominalsOfContinuousStates: Symbol<'static, fmi3GetNominalsOfContinuousStatesTYPE>,
    fmi3GetNumberOfEventIndicators: Symbol<'static, fmi3GetNumberOfEventIndicatorsTYPE>,
    fmi3GetNumberOfContinuousStates: Symbol<'static, fmi3GetNumberOfContinuousStatesTYPE>,
    fmi3EnterStepMode: Symbol<'static, fmi3EnterStepModeTYPE>,
    fmi3GetOutputDerivatives: Symbol<'static, fmi3GetOutputDerivativesTYPE>,
    fmi3DoStep: Symbol<'static, fmi3DoStepTYPE>,
    fmi3ActivateModelPartition: Symbol<'static, fmi3ActivateModelPartitionTYPE>,

    instance: fmi3Instance,
}

#[unsafe(no_mangle)]
pub extern "C" fn logMessage(
    instanceEnvironment: fmi3InstanceEnvironment,
    status: fmi3Status,
    category: fmi3String,
    message: fmi3String,
) {
    if instanceEnvironment.is_null() {
        return;
    }

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

    unsafe {
        let cb_ptr = instanceEnvironment as *mut Arc<LogMessageCallback>;
        let cb: &Arc<LogMessageCallback> = &*cb_ptr;
        cb(&status, &category_str, &message_str);
    }
}

fn get_symbol<T>(
    lib: &Library,
    symbol_name: &[u8],
) -> Result<Symbol<'static, T>, libloading::Error> {
    unsafe {
        let symbol: Symbol<T> = lib.get(symbol_name)?;
        Ok(std::mem::transmute(symbol))
    }
}

impl FMU3 {

    fn new(
        unzipdir: &Path,
        modelIdentifier: &str,
        logFMICall: Option<Box<LogFMICallCallback>>,
        logMessage: Option<Box<LogMessageCallback>>,
    ) -> Result<FMU3, Box<dyn Error>> {

        let shared_library_path = unzipdir
            .join("binaries")
            .join(PLATFORM_TUPLE)
            .join(format!("{modelIdentifier}{SHARED_LIBRARY_EXTENSION}"));

        if !shared_library_path.is_file() {
            return Err(format!("Missing shared library {shared_library_path:?}.").into())
        }

        let lib = Box::new(unsafe { Library::new(shared_library_path)? });

        /***************************************************
        Common Functions
        ****************************************************/

        let fmi3GetVersion = get_symbol::<fmi3GetVersionTYPE>(&lib, b"fmi3GetVersion")?;
        let fmi3SetDebugLogging =
            get_symbol::<fmi3SetDebugLoggingTYPE>(&lib, b"fmi3SetDebugLogging")?;
        let fmi3InstantiateModelExchange =
            get_symbol::<fmi3InstantiateModelExchangeTYPE>(&lib, b"fmi3InstantiateModelExchange")?;
        let fmi3InstantiateCoSimulation =
            get_symbol::<fmi3InstantiateCoSimulationTYPE>(&lib, b"fmi3InstantiateCoSimulation")?;
        let fmi3InstantiateScheduledExecution = get_symbol::<fmi3InstantiateScheduledExecutionTYPE>(
            &lib,
            b"fmi3InstantiateScheduledExecution",
        )?;
        let fmi3FreeInstance = get_symbol::<fmi3FreeInstanceTYPE>(&lib, b"fmi3FreeInstance")?;
        let fmi3EnterInitializationMode =
            get_symbol::<fmi3EnterInitializationModeTYPE>(&lib, b"fmi3EnterInitializationMode")?;
        let fmi3ExitInitializationMode =
            get_symbol::<fmi3ExitInitializationModeTYPE>(&lib, b"fmi3ExitInitializationMode")?;
        let fmi3EnterEventMode = get_symbol::<fmi3EnterEventModeTYPE>(&lib, b"fmi3EnterEventMode")?;
        let fmi3Terminate = get_symbol::<fmi3TerminateTYPE>(&lib, b"fmi3Terminate")?;
        let fmi3Reset = get_symbol::<fmi3ResetTYPE>(&lib, b"fmi3Reset")?;
        let fmi3GetFloat32 = get_symbol::<fmi3GetFloat32TYPE>(&lib, b"fmi3GetFloat32")?;
        let fmi3GetFloat64 = get_symbol::<fmi3GetFloat64TYPE>(&lib, b"fmi3GetFloat64")?;
        let fmi3GetInt8 = get_symbol::<fmi3GetInt8TYPE>(&lib, b"fmi3GetInt8")?;
        let fmi3GetUInt8 = get_symbol::<fmi3GetUInt8TYPE>(&lib, b"fmi3GetUInt8")?;
        let fmi3GetInt16 = get_symbol::<fmi3GetInt16TYPE>(&lib, b"fmi3GetInt16")?;
        let fmi3GetUInt16 = get_symbol::<fmi3GetUInt16TYPE>(&lib, b"fmi3GetUInt16")?;
        let fmi3GetInt32 = get_symbol::<fmi3GetInt32TYPE>(&lib, b"fmi3GetInt32")?;
        let fmi3GetUInt32 = get_symbol::<fmi3GetUInt32TYPE>(&lib, b"fmi3GetUInt32")?;
        let fmi3GetInt64 = get_symbol::<fmi3GetInt64TYPE>(&lib, b"fmi3GetInt64")?;
        let fmi3GetUInt64 = get_symbol::<fmi3GetUInt64TYPE>(&lib, b"fmi3GetUInt64")?;
        let fmi3GetBoolean = get_symbol::<fmi3GetBooleanTYPE>(&lib, b"fmi3GetBoolean")?;
        let fmi3GetString = get_symbol::<fmi3GetStringTYPE>(&lib, b"fmi3GetString")?;
        let fmi3GetBinary = get_symbol::<fmi3GetBinaryTYPE>(&lib, b"fmi3GetBinary")?;
        let fmi3GetClock = get_symbol::<fmi3GetClockTYPE>(&lib, b"fmi3GetClock")?;
        let fmi3SetFloat32 = get_symbol::<fmi3SetFloat32TYPE>(&lib, b"fmi3SetFloat32")?;
        let fmi3SetFloat64 = get_symbol::<fmi3SetFloat64TYPE>(&lib, b"fmi3SetFloat64")?;
        let fmi3SetInt8 = get_symbol::<fmi3SetInt8TYPE>(&lib, b"fmi3SetInt8")?;
        let fmi3SetUInt8 = get_symbol::<fmi3SetUInt8TYPE>(&lib, b"fmi3SetUInt8")?;
        let fmi3SetInt16 = get_symbol::<fmi3SetInt16TYPE>(&lib, b"fmi3SetInt16")?;
        let fmi3SetUInt16 = get_symbol::<fmi3SetUInt16TYPE>(&lib, b"fmi3SetUInt16")?;
        let fmi3SetInt32 = get_symbol::<fmi3SetInt32TYPE>(&lib, b"fmi3SetInt32")?;
        let fmi3SetUInt32 = get_symbol::<fmi3SetUInt32TYPE>(&lib, b"fmi3SetUInt32")?;
        let fmi3SetInt64 = get_symbol::<fmi3SetInt64TYPE>(&lib, b"fmi3SetInt64")?;
        let fmi3SetUInt64 = get_symbol::<fmi3SetUInt64TYPE>(&lib, b"fmi3SetUInt64")?;
        let fmi3SetBoolean = get_symbol::<fmi3SetBooleanTYPE>(&lib, b"fmi3SetBoolean")?;
        let fmi3SetString = get_symbol::<fmi3SetStringTYPE>(&lib, b"fmi3SetString")?;
        let fmi3SetBinary = get_symbol::<fmi3SetBinaryTYPE>(&lib, b"fmi3SetBinary")?;
        let fmi3SetClock = get_symbol::<fmi3SetClockTYPE>(&lib, b"fmi3SetClock")?;
        let fmi3GetNumberOfVariableDependencies = get_symbol::<
            fmi3GetNumberOfVariableDependenciesTYPE,
        >(
            &lib, b"fmi3GetNumberOfVariableDependencies"
        )?;
        let fmi3GetVariableDependencies =
            get_symbol::<fmi3GetVariableDependenciesTYPE>(&lib, b"fmi3GetVariableDependencies")?;
        let fmi3GetFMUState = get_symbol::<fmi3GetFMUStateTYPE>(&lib, b"fmi3GetFMUState")?;
        let fmi3SetFMUState = get_symbol::<fmi3SetFMUStateTYPE>(&lib, b"fmi3SetFMUState")?;
        let fmi3FreeFMUState = get_symbol::<fmi3FreeFMUStateTYPE>(&lib, b"fmi3FreeFMUState")?;
        let fmi3SerializedFMUStateSize =
            get_symbol::<fmi3SerializedFMUStateSizeTYPE>(&lib, b"fmi3SerializedFMUStateSize")?;
        let fmi3SerializeFMUState =
            get_symbol::<fmi3SerializeFMUStateTYPE>(&lib, b"fmi3SerializeFMUState")?;
        let fmi3DeserializeFMUState =
            get_symbol::<fmi3DeserializeFMUStateTYPE>(&lib, b"fmi3DeserializeFMUState")?;
        let fmi3GetDirectionalDerivative =
            get_symbol::<fmi3GetDirectionalDerivativeTYPE>(&lib, b"fmi3GetDirectionalDerivative")?;
        let fmi3GetAdjointDerivative =
            get_symbol::<fmi3GetAdjointDerivativeTYPE>(&lib, b"fmi3GetAdjointDerivative")?;
        let fmi3EnterConfigurationMode =
            get_symbol::<fmi3EnterConfigurationModeTYPE>(&lib, b"fmi3EnterConfigurationMode")?;
        let fmi3ExitConfigurationMode =
            get_symbol::<fmi3ExitConfigurationModeTYPE>(&lib, b"fmi3ExitConfigurationMode")?;
        let fmi3GetIntervalDecimal =
            get_symbol::<fmi3GetIntervalDecimalTYPE>(&lib, b"fmi3GetIntervalDecimal")?;
        let fmi3GetIntervalFraction =
            get_symbol::<fmi3GetIntervalFractionTYPE>(&lib, b"fmi3GetIntervalFraction")?;
        let fmi3GetShiftDecimal =
            get_symbol::<fmi3GetShiftDecimalTYPE>(&lib, b"fmi3GetShiftDecimal")?;
        let fmi3GetShiftFraction =
            get_symbol::<fmi3GetShiftFractionTYPE>(&lib, b"fmi3GetShiftFraction")?;
        let fmi3SetIntervalDecimal =
            get_symbol::<fmi3SetIntervalDecimalTYPE>(&lib, b"fmi3SetIntervalDecimal")?;
        let fmi3SetIntervalFraction =
            get_symbol::<fmi3SetIntervalFractionTYPE>(&lib, b"fmi3SetIntervalFraction")?;
        let fmi3SetShiftDecimal =
            get_symbol::<fmi3SetShiftDecimalTYPE>(&lib, b"fmi3SetShiftDecimal")?;
        let fmi3SetShiftFraction =
            get_symbol::<fmi3SetShiftFractionTYPE>(&lib, b"fmi3SetShiftFraction")?;
        let fmi3EvaluateDiscreteStates =
            get_symbol::<fmi3EvaluateDiscreteStatesTYPE>(&lib, b"fmi3EvaluateDiscreteStates")?;
        let fmi3UpdateDiscreteStates =
            get_symbol::<fmi3UpdateDiscreteStatesTYPE>(&lib, b"fmi3UpdateDiscreteStates")?;
        let fmi3EnterContinuousTimeMode =
            get_symbol::<fmi3EnterContinuousTimeModeTYPE>(&lib, b"fmi3EnterContinuousTimeMode")?;
        let fmi3CompletedIntegratorStep =
            get_symbol::<fmi3CompletedIntegratorStepTYPE>(&lib, b"fmi3CompletedIntegratorStep")?;
        let fmi3SetTime = get_symbol::<fmi3SetTimeTYPE>(&lib, b"fmi3SetTime")?;
        let fmi3SetContinuousStates =
            get_symbol::<fmi3SetContinuousStatesTYPE>(&lib, b"fmi3SetContinuousStates")?;
        let fmi3GetContinuousStateDerivatives = get_symbol::<fmi3GetContinuousStateDerivativesTYPE>(
            &lib,
            b"fmi3GetContinuousStateDerivatives",
        )?;
        let fmi3GetEventIndicators =
            get_symbol::<fmi3GetEventIndicatorsTYPE>(&lib, b"fmi3GetEventIndicators")?;
        let fmi3GetContinuousStates =
            get_symbol::<fmi3GetContinuousStatesTYPE>(&lib, b"fmi3GetContinuousStates")?;
        let fmi3GetNominalsOfContinuousStates = get_symbol::<fmi3GetNominalsOfContinuousStatesTYPE>(
            &lib,
            b"fmi3GetNominalsOfContinuousStates",
        )?;
        let fmi3GetNumberOfEventIndicators = get_symbol::<fmi3GetNumberOfEventIndicatorsTYPE>(
            &lib,
            b"fmi3GetNumberOfEventIndicators",
        )?;
        let fmi3GetNumberOfContinuousStates = get_symbol::<fmi3GetNumberOfContinuousStatesTYPE>(
            &lib,
            b"fmi3GetNumberOfContinuousStates",
        )?;
        let fmi3EnterStepMode = get_symbol::<fmi3EnterStepModeTYPE>(&lib, b"fmi3EnterStepMode")?;
        let fmi3GetOutputDerivatives =
            get_symbol::<fmi3GetOutputDerivativesTYPE>(&lib, b"fmi3GetOutputDerivatives")?;
        let fmi3DoStep = get_symbol::<fmi3DoStepTYPE>(&lib, b"fmi3DoStep")?;
        let fmi3ActivateModelPartition =
            get_symbol::<fmi3ActivateModelPartitionTYPE>(&lib, b"fmi3ActivateModelPartition")?;

        Ok(FMU3 {
            logFMICall: logFMICall.map(|cb| Arc::from(cb)),
            logMessage: logMessage.map(|cb| Arc::from(cb)),
            _lib: lib,
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

    pub fn getVersion(&self) -> String {
        let version = unsafe {
            let version_cstr = (self.fmi3GetVersion)();
            CStr::from_ptr(version_cstr).to_string_lossy().into_owned()
        };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3GetVersion() -> \"{version}\"");
            cb(&fmi3OK, message.as_str());
        }
        version
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
        requiredIntermediateVariables: &[c_uint],
        logFMICall: Option<Box<LogFMICallCallback>>,
        logMessage: Option<Box<LogMessageCallback>>,
    ) -> Result<FMU3, Box<dyn Error>> {
        
        let mut fmu = FMU3::new(unzipdir, modelIdentifier, logFMICall, logMessage)?;

        let resource_path = unzipdir.join("resources").join("");

        let resourcePath = if resource_path.is_dir() {
            Some(resource_path.as_path())
        } else {
            None
        };

        fmu.instance = fmu._instantiateCoSimulation(instanceName, instantiationToken, resourcePath, visible, loggingOn, eventModeUsed, earlyReturnAllowed, requiredIntermediateVariables);

        if fmu.instance.is_null() {
            Err("Failed to instantiate FMU.".into())
        } else {
            Ok(fmu)
        }
    }

    fn _instantiateCoSimulation(
        &mut self,
        instanceName: &str,
        instantiationToken: &str,
        resourcePath: Option<&Path>,
        visible: bool,
        loggingOn: bool,
        eventModeUsed: bool,
        earlyReturnAllowed: bool,
        requiredIntermediateVariables: &[c_uint],
    ) -> fmi3Instance {
        let instance_name_cstr = CString::new(instanceName).unwrap();

        let instantiation_token_cstr = CString::new(instantiationToken).unwrap();

        let resource_path_cstr = resourcePath
            .map(|path| CString::new(path.to_string_lossy().as_ref()).ok())
            .flatten();

        let path_ptr = resource_path_cstr
            .as_ref()
            .map(|cstr| cstr.as_ptr())
            .unwrap_or(ptr::null());

        let userdata = if let Some(callback) = self.logMessage.take() {
            Box::into_raw(Box::new(callback)) as *mut c_void
        } else {
            ptr::null_mut()
        };

        let logMessage_ptr = logMessage as *const c_void;

        let intermediateUpdate_ptr = ptr::null();

        let instance = unsafe {
            (self.fmi3InstantiateCoSimulation)(
                instance_name_cstr.as_ptr(),
                instantiation_token_cstr.as_ptr(),
                path_ptr,
                visible,
                loggingOn,
                eventModeUsed,
                earlyReturnAllowed,
                requiredIntermediateVariables.as_ptr(),
                requiredIntermediateVariables.len(),
                userdata,
                logMessage_ptr,
                intermediateUpdate_ptr,
            )
        };

        let status = if self.instance.is_null() {
            fmi3Error
        } else {
            fmi3OK
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3InstantiateCoSimulation(instanceName=\"{}\", instantiationToken=\"{}\", resourcePath={:?}, visible={}, loggingOn={}, eventModeUsed={}, earlyReturnAllowed={}, nRequiredIntermediateVariables={}, instanceEnvironment={:p}, logMessage={:p}, intermediateUpdate={:p})",
                instanceName,
                instantiationToken,
                resourcePath,
                visible,
                loggingOn,
                eventModeUsed,
                earlyReturnAllowed,
                requiredIntermediateVariables.len(),
                userdata,
                logMessage_ptr,
                intermediateUpdate_ptr
            );
            cb(&status, &message);
        }

        instance
    }

    pub fn terminate(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3Terminate)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3Termiate()");
            cb(&status, &message);
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
                self.instance,
                toleranceDefined,
                tolerance,
                startTime,
                stopTimeDefined,
                stopTime,
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3EnterInitializationMode(toleranceDefined={}, tolerance={}, startTime={}, stopTimeDefined={}, stopTime={})",
                toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime
            );
            cb(&status, &message);
        }

        status
    }

    pub fn exitInitializationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3ExitInitializationMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3ExitInitializationMode()");
            cb(&status, &message);
        }
        status
    }

    pub fn reset(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3Reset)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3Reset()");
            cb(&status, &message);
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3DoStep(currentCommunicationPoint={}, communicationStepSize={}, noSetFMUStatePriorToCurrentPoint={}, eventHandlingNeeded={:?}, terminateSimulation={:?}, earlyReturn={:?}, lastSuccessfulTime={:?})",
                currentCommunicationPoint,
                communicationStepSize,
                noSetFMUStatePriorToCurrentPoint,
                eventHandlingNeeded,
                terminateSimulation,
                earlyReturn,
                lastSuccessfulTime,
            );
            cb(&status, &message);
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
        
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetString(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={})",
                valueReferences,
                valueReferences.len(),
                values,
                values.len()
            );
            cb(&status, &message);
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
        sizes: &mut [usize],
        values: &mut [fmi3Binary],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3GetBinary)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                sizes.as_mut_ptr(),
                values.as_mut_ptr(),
                values.len(),
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetBinary(valueReferences={:?}, nValueReferences={}, sizes={:?}, values={:?}, nValues={})",
                valueReferences,
                valueReferences.len(),
                sizes,
                values,
                values.len(),
            );
            cb(&status, &message);
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetString(valueReferences={:?}, nValueReferences={}, values={:?}, nValues={})",
                valueReferences,
                valueReferences.len(),
                values,
                values.len()
            );
            cb(&status, &message);
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
        sizes: &[usize],
        values: &[fmi3Binary],
    ) -> fmi3Status {
        let status = unsafe {
            (self.fmi3SetBinary)(
                self.instance,
                valueReferences.as_ptr(),
                valueReferences.len(),
                sizes.as_ptr(),
                values.as_ptr(),
                values.len(),
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetBinary(valueReferences={:?}, nValueReferences={}, sizes={:?}, values={:?}, nValues={})",
                valueReferences,
                valueReferences.len(),
                sizes,
                values,
                values.len(),
            );
            cb(&status, &message);
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetDebugLogging(loggingOn={}, nCategories={})",
                loggingOn,
                categories.len(),
            );
            cb(&status, &message);
        }

        status
    }

    pub fn enterEventMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterEventMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3EnterEventMode()");
            cb(&status, &message);
        }
        status
    }

    pub fn enterStepMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterStepMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3EnterStepMode()");
            cb(&status, &message);
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetNumberOfVariableDependencies(valueReference={}) -> {:?}, nDependencies={}",
                valueReference, status, nDependencies
            );

            cb(&status, &message);
        }

        if status == fmi3OK {
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetVariableDependencies(valueReference={})",
                valueReference
            );

            cb(&status, &message);
        }

        status
    }

    pub fn getFMUState(&self) -> Result<fmi3FMUState, fmi3Status> {
        let mut fmuState: fmi3FMUState = ptr::null_mut();
        let status = unsafe { (self.fmi3GetFMUState)(self.instance, &mut fmuState) };

        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3GetFMUState()");

            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok(fmuState)
        } else {
            Err(status)
        }
    }

    pub fn setFMUState(&self, fmuState: fmi3FMUState) -> fmi3Status {
        let status = unsafe { (self.fmi3SetFMUState)(self.instance, fmuState) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3SetFMUState()");
            cb(&status, &message);
        }
        status
    }

    pub fn freeFMUState(&self, fmuState: &mut fmi3FMUState) -> fmi3Status {
        let status = unsafe { (self.fmi3FreeFMUState)(self.instance, fmuState) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3FreeFMUState()");
            cb(&status, &message);
        }
        status
    }

    pub fn serializedFMUStateSize(&self, fmuState: fmi3FMUState) -> Result<usize, fmi3Status> {
        let mut size: usize = 0;
        let status =
            unsafe { (self.fmi3SerializedFMUStateSize)(self.instance, fmuState, &mut size) };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SerializedFMUStateSize() -> {:?}, size={}",
                status, size
            );
            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok(size)
        } else {
            Err(status)
        }
    }

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

        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3SerializeFMUState(size={})", serializedState.len(),);
            cb(&status, &message);
        }
        status
    }

    pub fn deserializeFMUState(
        &self,
        serializedState: &[fmi3Byte],
    ) -> Result<fmi3FMUState, fmi3Status> {
        let mut fmuState: fmi3FMUState = ptr::null_mut();
        let status = unsafe {
            (self.fmi3DeserializeFMUState)(
                self.instance,
                serializedState.as_ptr(),
                serializedState.len(),
                &mut fmuState,
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3DeserializeFMUState(size={})", serializedState.len(),);
            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok(fmuState)
        } else {
            Err(status)
        }
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetDirectionalDerivative(nUnknowns={}, nKnowns={})",
                unknowns.len(),
                knowns.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetAdjointDerivative(nUnknowns={}, nKnowns={})",
                unknowns.len(),
                knowns.len(),
            );
            cb(&status, &message);
        }
        status
    }

    pub fn enterConfigurationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterConfigurationMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3EnterConfigurationMode()");
            cb(&status, &message);
        }
        status
    }

    pub fn exitConfigurationMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3ExitConfigurationMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3ExitConfigurationMode()");
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetIntervalDecimal(nValueReferences={})",
                valueReferences.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetIntervalFraction(nValueReferences={})",
                valueReferences.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetIntervalDecimal(nValueReferences={})",
                valueReferences.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetIntervalFraction(nValueReferences={})",
                valueReferences.len(),
            );
            cb(&status, &message);
        }
        status
    }

    pub fn enterContinuousTimeMode(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EnterContinuousTimeMode)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3EnterContinuousTimeMode()");
            cb(&status, &message);
        }
        status
    }

    pub fn completedIntegratorStep(
        &self,
        noSetFMUStatePriorToCurrentPoint: fmi3Boolean,
    ) -> Result<(fmi3Boolean, fmi3Boolean), fmi3Status> {
        let mut enterEventMode = false;
        let mut terminateSimulation = false;

        let status = unsafe {
            (self.fmi3CompletedIntegratorStep)(
                self.instance,
                noSetFMUStatePriorToCurrentPoint,
                &mut enterEventMode,
                &mut terminateSimulation,
            )
        };
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3CompletedIntegratorStep() -> {:?}, enterEventMode={}, terminateSimulation={}",
                status, enterEventMode, terminateSimulation
            );
            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok((enterEventMode, terminateSimulation))
        } else {
            Err(status)
        }
    }

    pub fn setTime(&self, time: fmi3Float64) -> fmi3Status {
        let status = unsafe { (self.fmi3SetTime)(self.instance, time) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3SetTime(time={})", time);
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3SetContinuousStates(nContinuousStates={})",
                continuousStates.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetContinuousStates(nContinuousStates={})",
                continuousStates.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetContinuousStateDerivatives(nContinuousStates={})",
                derivatives.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetEventIndicators(nEventIndicators={})",
                eventIndicators.len(),
            );
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetNominalsOfContinuousStates(nNominals={})",
                nominals.len(),
            );
            cb(&status, &message);
        }
        status
    }

    pub fn getNumberOfEventIndicators(&self) -> Result<usize, fmi3Status> {
        let mut nEventIndicators: usize = 0;
        let status =
            unsafe { (self.fmi3GetNumberOfEventIndicators)(self.instance, &mut nEventIndicators) };
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetNumberOfEventIndicators() -> {:?}, nEventIndicators={}",
                status, nEventIndicators
            );
            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok(nEventIndicators)
        } else {
            Err(status)
        }
    }

    pub fn getNumberOfContinuousStates(&self) -> Result<usize, fmi3Status> {
        let mut nContinuousStates: usize = 0;
        let status = unsafe {
            (self.fmi3GetNumberOfContinuousStates)(self.instance, &mut nContinuousStates)
        };
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetNumberOfContinuousStates() -> {:?}, nContinuousStates={}",
                status, nContinuousStates
            );
            cb(&status, &message);
        }

        if status == fmi3OK {
            Ok(nContinuousStates)
        } else {
            Err(status)
        }
    }

    pub fn evaluateDiscreteStates(&self) -> fmi3Status {
        let status = unsafe { (self.fmi3EvaluateDiscreteStates)(self.instance) };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3EvaluateDiscreteStates()");
            cb(&status, &message);
        }
        status
    }

    pub fn updateDiscreteStates(
        &self,
        discreteStatesNeedUpdate: &mut fmi3Boolean,
        terminateSimulation: &mut fmi3Boolean,
        nominalsOfContinuousStatesChanged: &mut fmi3Boolean,
        valuesOfContinuousStatesChanged: &mut fmi3Boolean,
        nextEventTimeDefined: &mut fmi3Boolean,
        nextEventTime: &mut fmi3Float64,
    ) -> fmi3Status {

        let status = unsafe {
            (self.fmi3UpdateDiscreteStates)(
                self.instance,
                discreteStatesNeedUpdate,
                terminateSimulation,
                nominalsOfContinuousStatesChanged,
                valuesOfContinuousStatesChanged,
                nextEventTimeDefined,
                nextEventTime,
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi3UpdateDiscreteStates(discreteStatesNeedUpdate={discreteStatesNeedUpdate}, terminateSimulation={terminateSimulation}, nominalsOfContinuousStatesChanged={nominalsOfContinuousStatesChanged}, valuesOfContinuousStatesChanged={valuesOfContinuousStatesChanged}, nextEventTimeDefined={nextEventTimeDefined}, nextEventTime={nextEventTime})");
            cb(&status, &message);
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
        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3GetOutputDerivatives(nValueReferences={})",
                valueReferences.len(),
            );
            cb(&status, &message);
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

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi3ActivateModelPartition(clockReference={}, activationTime={}, priority={})",
                clockReference, activationTime, priority
            );
            cb(&status, &message);
        }

        status
    }
}

// Explicitly implement Sync for FMU3 since all fields are Sync
unsafe impl Sync for FMU3 {}