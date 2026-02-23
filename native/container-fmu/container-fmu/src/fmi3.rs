#![allow(non_camel_case_types, non_snake_case, unused_variables)]

use crate::*;
use fmi::fmi2::types::*;
use fmi::fmi3::types::*;
use std::ffi::{CStr, CString};
use std::os::raw::c_void;
use std::path::Path;
use std::ptr;
use std::sync::Arc;

fn NOT_IMPLEMENTED(instance: fmi3Instance) -> fmi3Status {
    if instance.is_null() {
        return fmi3Fatal;
    }
    let container: &mut Container = unsafe { &mut *(instance as *mut Container) };
    container.logError("Function is not implemented.");
    fmi3Error
}

macro_rules! get_container {
    ($instance:expr) => {{
        if $instance.is_null() {
            eprintln!("Argument instance must not be NULL.");
            return fmi2Error;
        }
        unsafe { &mut *($instance as *mut Container) }
    }};
}

/* Inquire version numbers and setting logging status */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetVersion() -> fmi3String {
    b"3.0\0".as_ptr() as fmi3String
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetDebugLogging(
    instance: fmi3Instance,
    loggingOn: fmi3Boolean,
    nCategories: usize,
    categories: *const fmi3String,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Creation and destruction of FMU instances and setting debug status */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3InstantiateModelExchange(
    instanceName: fmi3String,
    instantiationToken: fmi3String,
    resourcePath: fmi3String,
    visible: fmi3Boolean,
    loggingOn: fmi3Boolean,
    instanceEnvironment: fmi3InstanceEnvironment,
    logMessage: Option<fmi3LogMessageCallback>,
) -> fmi3Instance {
    if let Some(callback) = logMessage {
        let message = CString::new("Function is not implemented.").unwrap();
        unsafe {
            (callback)(
                instanceEnvironment,
                fmi3Error,
                LOG_STATUS_ERROR,
                message.as_ptr(),
            )
        };
    }

    ptr::null_mut()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3InstantiateCoSimulation(
    instanceName: fmi3String,
    instantiationToken: fmi3String,
    resourcePath: fmi3String,
    visible: fmi3Boolean,
    loggingOn: fmi3Boolean,
    eventModeUsed: fmi3Boolean,
    earlyReturnAllowed: fmi3Boolean,
    requiredIntermediateVariables: *const fmi3ValueReference,
    nRequiredIntermediateVariables: usize,
    instanceEnvironment: fmi3InstanceEnvironment,
    logMessage: Option<fmi3LogMessageCallback>,
    intermediateUpdate: fmi3IntermediateUpdateCallback,
) -> fmi3Instance {
    if let None = logMessage {
        return ptr::null_mut();
    }

    let logMessage = logMessage.unwrap();

    let log_error = |message: &str| {
        let message = CString::new(message).unwrap();
        unsafe {
            logMessage(
                instanceEnvironment,
                fmi3Error,
                LOG_STATUS_ERROR,
                message.as_ptr(),
            )
        };
    };

    if instantiationToken.is_null() {
        log_error("Argument instantiationToken must not be NULL.");
        return ptr::null_mut();
    }

    let instantiation_token = unsafe { CStr::from_ptr(instantiationToken) };
    let instantiation_token = instantiation_token.to_string_lossy().into_owned();

    if resourcePath.is_null() {
        log_error("Argument resourcePath must not be NULL.");
        return ptr::null_mut();
    }

    let resource_path = unsafe { CStr::from_ptr(resourcePath) };
    let resource_path = Path::new(resource_path.to_str().unwrap());

    // Convert raw pointer to thread-safe representation
    let instance_env_ptr = instanceEnvironment as usize;

    let log_message = move |status: &fmiStatus, category: &str, message: &str| {
        let message = CString::new(message).unwrap();
        unsafe {
            logMessage(
                instance_env_ptr as *mut std::os::raw::c_void,
                *status,
                LOG_STATUS_ERROR,
                message.as_ptr(),
            )
        };
    };

    let log_fmi_call = move |status: &fmiStatus, component: &str, message: &str| {
        let message = format!("[{component}] {message}");
        let message = CString::new(message).unwrap();
        unsafe {
            logMessage(
                instance_env_ptr as *mut std::os::raw::c_void,
                *status,
                LOG_FMI_CALLS,
                message.as_ptr(),
            )
        };
    };

    match Container::instantiate(
        &instantiation_token,
        resource_path,
        Arc::new(log_message),
        Arc::new(log_fmi_call),
        loggingOn,
        visible,
        instanceEnvironment,
    ) {
        Ok(container) => {
            let container = Box::new(container);
            Box::into_raw(container) as fmi3Instance
        }
        Err(error) => {
            log_error(&error);
            ptr::null_mut()
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3InstantiateScheduledExecution(
    instanceName: fmi3String,
    instantiationToken: fmi3String,
    resourcePath: fmi3String,
    visible: fmi3Boolean,
    loggingOn: fmi3Boolean,
    instanceEnvironment: fmi3InstanceEnvironment,
    logMessage: Option<fmi3LogMessageCallback>,
    clockUpdate: Option<fmi3ClockUpdateCallback>,
    lockPreemption: Option<fmi3LockPreemptionCallback>,
    unlockPreemption: Option<fmi3UnlockPreemptionCallback>,
) -> fmi3Instance {
    if let Some(callback) = logMessage {
        let message = CString::new("Function is not implemented.").unwrap();
        unsafe {
            (callback)(
                instanceEnvironment,
                fmi3Error,
                LOG_STATUS_ERROR,
                message.as_ptr(),
            )
        };
    }

    ptr::null_mut()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3FreeInstance(instance: fmi3Instance) {
    if instance.is_null() {
        return;
    }

    unsafe {
        let _ = Box::from_raw(instance as *mut Container);
        // Box is dropped here, memory is freed
    }
}

/* Enter and exit initialization mode, enter event mode, terminate and reset */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EnterInitializationMode(
    instance: fmi3Instance,
    toleranceDefined: bool,
    tolerance: fmi3Float64,
    startTime: fmi3Float64,
    stopTimeDefined: bool,
    stopTime: fmi3Float64,
) -> fmi3Status {
    let container = get_container!(instance);
    container.tolerance = if toleranceDefined {
        Some(tolerance)
    } else {
        None
    };
    container.startTime = startTime;
    container.stopTime = if stopTimeDefined {
        Some(stopTime)
    } else {
        None
    };
    container.enterInitializationMode()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3ExitInitializationMode(instance: fmi3Instance) -> fmi3Status {
    let container = get_container!(instance);
    container.exitInitializationMode()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EnterEventMode(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3Terminate(instance: fmi3Instance) -> fmi3Status {
    let container = get_container!(instance);
    container.terminate()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3Reset(instance: fmi3Instance) -> fmi3Status {
    let container = get_container!(instance);
    container.reset()
}

/* Getting and setting variable values */

macro_rules! make_getter {
    ($name:ident, $type:ident, $getter:ident) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $name(
            instance: fmi3Instance,
            valueReferences: *const fmi3ValueReference,
            nValueReferences: usize,
            values: *mut $type,
            nValues: usize,
        ) -> fmi3Status {
            if instance.is_null() {
                eprintln!("Argument instance must not be NULL.");
                return fmi3Error;
            }

            let container = unsafe { &*(instance as *mut Container) };

            if valueReferences.is_null() {
                container.logError("Argument valueReferences must not be NULL.");
                return fmi3Error;
            }

            if values.is_null() {
                container.logError("Argument values must not be NULL.");
                return fmi3Error;
            }

            let valueReferences =
                unsafe { std::slice::from_raw_parts(valueReferences, nValueReferences) };

            let values = unsafe { std::slice::from_raw_parts_mut(values, nValues) };

            container.$getter(valueReferences, values)
        }
    };
}

make_getter!(fmi3GetFloat32, fmi3Float32, getFloat32);
make_getter!(fmi3GetFloat64, fmi3Float64, getFloat64);
make_getter!(fmi3GetInt8, fmi3Int8, getInt8);
make_getter!(fmi3GetUInt8, fmi3UInt8, getUInt8);
make_getter!(fmi3GetInt16, fmi3Int16, getInt16);
make_getter!(fmi3GetUInt16, fmi3UInt16, getUInt16);
make_getter!(fmi3GetInt32, fmi3Int32, getInt32);
make_getter!(fmi3GetUInt32, fmi3UInt32, getUInt32);
make_getter!(fmi3GetInt64, fmi3Int64, getInt64);
make_getter!(fmi3GetUInt64, fmi3UInt64, getUInt64);
make_getter!(fmi3GetBoolean, fmi3Boolean, getBoolean);
// make_getter!(fmi3GetString, fmi3String, getString);

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetString(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    values: *mut fmi3String,
    nValues: usize,
) -> fmi3Status {
    if instance.is_null() {
        eprintln!("Argument instance must not be NULL.");
        return fmi3Error;
    }

    let container = unsafe { &mut *(instance as *mut Container) };

    if valueReferences.is_null() {
        container.logError("Argument valueReferences must not be NULL.");
        return fmi3Error;
    }

    if values.is_null() {
        container.logError("Argument values must not be NULL.");
        return fmi3Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(valueReferences, nValueReferences) };
    let values = unsafe { std::slice::from_raw_parts_mut(values, nValueReferences) };

    let mut buffer = vec![String::new(); values.len()];

    let status = container.getString(valueReferences, buffer.as_mut());

    container
        .stringValues
        .resize(values.len(), CString::new("").unwrap());

    for (i, v) in buffer.iter().enumerate() {
        container.stringValues[i] = CString::new(v.as_str()).unwrap();
        values[i] = container.stringValues[i].as_ptr();
    }

    status
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetBinary(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    valueSizes: *mut usize,
    values: *mut fmi3Binary,
    nValues: usize,
) -> fmi3Status {
    if instance.is_null() {
        eprintln!("Argument instance must not be NULL.");
        return fmi3Error;
    }

    let container = unsafe { &*(instance as *mut Container) };

    if valueReferences.is_null() {
        container.logError("Argument valueReferences must not be NULL.");
        return fmi3Error;
    }

    if valueSizes.is_null() {
        container.logError("Argument valueSizes must not be NULL.");
        return fmi3Error;
    }

    if values.is_null() {
        container.logError("Argument values must not be NULL.");
        return fmi3Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(valueReferences, nValueReferences) };
    let sizes = unsafe { std::slice::from_raw_parts_mut(valueSizes, nValues) };
    let values = unsafe { std::slice::from_raw_parts_mut(values, nValues) };

    container.getBinary(valueReferences, sizes, values)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetClock(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    values: *mut fmi3Clock,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

macro_rules! make_setter {
    ($name:ident, $type:ident, $setter:ident) => {
        #[unsafe(no_mangle)]
        pub extern "C" fn $name(
            instance: fmi3Instance,
            valueReferences: *const fmi3ValueReference,
            nValueReferences: usize,
            values: *const $type,
            nValues: usize,
        ) -> fmi3Status {
            if instance.is_null() {
                eprintln!("Argument instance must not be NULL.");
                return fmi3Error;
            }

            let container = unsafe { &*(instance as *mut Container) };

            if valueReferences.is_null() {
                container.logError("Argument valueReferences must not be NULL.");
                return fmi3Error;
            }

            if values.is_null() {
                container.logError("Argument values must not be NULL.");
                return fmi3Error;
            }

            let valueReferences =
                unsafe { std::slice::from_raw_parts(valueReferences, nValueReferences) };

            let values = unsafe { std::slice::from_raw_parts(values, nValues) };

            container.$setter(valueReferences, values)
        }
    };
}

make_setter!(fmi3SetFloat32, fmi3Float32, setFloat32);
make_setter!(fmi3SetFloat64, fmi3Float64, setFloat64);
make_setter!(fmi3SetInt8, fmi3Int8, setInt8);
make_setter!(fmi3SetUInt8, fmi3UInt8, setUInt8);
make_setter!(fmi3SetInt16, fmi3Int16, setInt16);
make_setter!(fmi3SetUInt16, fmi3UInt16, setUInt16);
make_setter!(fmi3SetInt32, fmi3Int32, setInt32);
make_setter!(fmi3SetUInt32, fmi3UInt32, setUInt32);
make_setter!(fmi3SetInt64, fmi3Int64, setInt64);
make_setter!(fmi3SetUInt64, fmi3UInt64, setUInt64);
make_setter!(fmi3SetBoolean, fmi3Boolean, setBoolean);
// make_setter!(fmi3SetString, fmi3String, setString);

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetString(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    values: *const fmi3String,
    nValues: usize,
) -> fmi3Status {
    if instance.is_null() {
        eprintln!("Argument instance must not be NULL.");
        return fmi3Error;
    }

    let container = unsafe { &*(instance as *mut Container) };

    if valueReferences.is_null() {
        container.logError("Argument valueReferences must not be NULL.");
        return fmi3Error;
    }

    if values.is_null() {
        container.logError("Argument values must not be NULL.");
        return fmi3Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(valueReferences, nValueReferences) };
    let values_slice = unsafe { std::slice::from_raw_parts(values, nValues) };

    let values_vec: Vec<String> = values_slice
        .iter()
        .map(|&v| unsafe { CStr::from_ptr(v).to_string_lossy().into_owned() })
        .collect();

    let v: Vec<&str> = values_vec.iter().map(|v| v.as_str()).collect();

    container.setString(valueReferences, &v)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetBinary(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    sizes: *const usize,
    values: *const *const u8,
    nValues: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetClock(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    values: *const u32,
    nValues: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Getting Variable Dependency Information */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetNumberOfVariableDependencies(
    instance: fmi3Instance,
    valueReference: fmi3ValueReference,
    nDependencies: *mut usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetVariableDependencies(
    instance: fmi3Instance,
    valueReference: fmi3ValueReference,
    elementIndicesOfDependent: *mut usize,
    independentVariables: *mut fmi3ValueReference,
    elementIndicesOfIndependents: *mut usize,
    dependencyKinds: *mut i32,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Getting and setting the internal FMU state */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetFMUState(
    instance: fmi3Instance,
    FMUState: *mut *mut c_void,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetFMUState(instance: fmi3Instance, FMUState: *mut c_void) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3FreeFMUState(
    instance: fmi3Instance,
    FMUState: *mut *mut c_void,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SerializedFMUStateSize(
    instance: fmi3Instance,
    FMUState: *mut c_void,
    size: *mut usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SerializeFMUState(
    instance: fmi3Instance,
    FMUState: *mut c_void,
    serializedState: *mut u8,
    size: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3DeserializeFMUState(
    instance: fmi3Instance,
    serializedState: *const u8,
    size: usize,
    FMUState: *mut *mut c_void,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Getting partial derivatives */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetDirectionalDerivative(
    instance: fmi3Instance,
    unknowns: *const fmi3ValueReference,
    nUnknowns: usize,
    knowns: *const fmi3ValueReference,
    nKnowns: usize,
    seed: *const fmi3Float64,
    nSeed: usize,
    sensitivity: *mut fmi3Float64,
    nSensitivity: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetAdjointDerivative(
    instance: fmi3Instance,
    unknowns: *const fmi3ValueReference,
    nUnknowns: usize,
    knowns: *const fmi3ValueReference,
    nKnowns: usize,
    seed: *const fmi3Float64,
    nSeed: usize,
    sensitivity: *mut fmi3Float64,
    nSensitivity: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Entering and exiting the Configuration or Reconfiguration Mode */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EnterConfigurationMode(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3ExitConfigurationMode(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetIntervalDecimal(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    intervals: *mut fmi3Float64,
    qualifiers: *mut fmi3IntervalQualifier,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetIntervalFraction(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    counters: *mut fmi3UInt64,
    resolutions: *mut fmi3UInt64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetShiftDecimal(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    shifts: *mut fmi3Float64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetShiftFraction(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    counters: *mut fmi3UInt64,
    resolutions: *mut fmi3UInt64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetIntervalDecimal(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    intervals: *const fmi3Float64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetIntervalFraction(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    counters: *const fmi3UInt64,
    resolutions: *const fmi3UInt64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetShiftDecimal(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    shifts: *const fmi3Float64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetShiftFraction(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    counters: *const fmi3UInt64,
    resolutions: *const fmi3UInt64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EvaluateDiscreteStates(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3UpdateDiscreteStates(
    instance: fmi3Instance,
    discreteStatesNeedUpdate: *mut fmi3Boolean,
    terminateSimulation: *mut fmi3Boolean,
    nominalsOfContinuousStatesChanged: *mut fmi3Boolean,
    valuesOfContinuousStatesChanged: *mut fmi3Boolean,
    nextEventTime: *mut fmi3Float64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/***************************************************
Types for Functions for Model Exchange
****************************************************/

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EnterContinuousTimeMode(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3CompletedIntegratorStep(
    instance: fmi3Instance,
    noSetFMUStatePriorToCurrentPoint: fmi3Boolean,
    enterEventMode: *mut fmi3Boolean,
    terminateSimulation: *mut fmi3Boolean,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/* Providing independent variables and re-initialization of caching */

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetTime(instance: fmi3Instance, time: fmi3Float64) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3SetContinuousStates(
    instance: fmi3Instance,
    continuousStates: *const fmi3Float64,
    nContinuousStates: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetContinuousStateDerivatives(
    instance: fmi3Instance,
    derivatives: *mut fmi3Float64,
    nContinuousStates: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetEventIndicators(
    instance: fmi3Instance,
    eventIndicators: *mut fmi3Float64,
    nEventIndicators: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetContinuousStates(
    instance: fmi3Instance,
    continuousStates: *mut fmi3Float64,
    nContinuousStates: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetNominalsOfContinuousStates(
    instance: fmi3Instance,
    nominals: *mut fmi3Float64,
    nNominals: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetNumberOfEventIndicators(
    instance: fmi3Instance,
    nEventIndicators: *mut usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetNumberOfContinuousStates(
    instance: fmi3Instance,
    nContinuousStates: *mut usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

/***************************************************
Types for Functions for Co-Simulation
****************************************************/

#[unsafe(no_mangle)]
pub extern "C" fn fmi3EnterStepMode(instance: fmi3Instance) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3GetOutputDerivatives(
    instance: fmi3Instance,
    valueReferences: *const fmi3ValueReference,
    nValueReferences: usize,
    orders: *const fmi3Int32,
    values: *mut fmi3Float64,
    nValues: usize,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi3DoStep(
    instance: fmi3Instance,
    currentCommunicationPoint: fmi3Float64,
    communicationStepSize: fmi3Float64,
    noSetFMUStatePriorToCurrentPoint: fmi3Boolean,
    eventHandlingNeeded: *mut fmi3Boolean,
    terminateSimulation: *mut fmi3Boolean,
    earlyReturn: *mut fmi3Boolean,
    lastSuccessfulTime: *mut fmi3Float64,
) -> fmi3Status {
    let container = get_container!(instance);

    if eventHandlingNeeded.is_null() {
        container.logError("Argument eventHandlingNeeded must not be NULL.");
        return fmi3Error;
    }

    if terminateSimulation.is_null() {
        container.logError("Argument terminateSimulation must not be NULL.");
        return fmi3Error;
    }

    if earlyReturn.is_null() {
        container.logError("Argument earlyReturn must not be NULL.");
        return fmi3Error;
    }

    if lastSuccessfulTime.is_null() {
        container.logError("Argument lastSuccessfulTime must not be NULL.");
        return fmi3Error;
    }

    let status = container.doStep(currentCommunicationPoint, communicationStepSize);

    unsafe {
        *eventHandlingNeeded = false;
        *terminateSimulation = container.terminated;
        *earlyReturn = false;
        *lastSuccessfulTime = container.time();
    };

    status
}

/***************************************************
Types for Functions for Scheduled Execution
****************************************************/

#[unsafe(no_mangle)]
pub extern "C" fn fmi3ActivateModelPartition(
    instance: fmi3Instance,
    clockReference: fmi3ValueReference,
    activationTime: fmi3Float64,
) -> fmi3Status {
    NOT_IMPLEMENTED(instance)
}
