#![allow(non_camel_case_types, non_snake_case, unused_variables)]

use crate::{Container, LOG_FMI_CALLS, LOG_STATUS_ERROR};
use fmi::fmi2::types::*;
use fmi::types::fmiStatus;
use fmi::types::*;
use std::ffi::{CStr, CString};
use std::ptr::null_mut;
use std::sync::Arc;
use url::Url;

fn NOT_IMPLEMENTED(c: fmi2Component) -> fmi2Status {
    if c.is_null() {
        return fmi2Fatal;
    }
    let container: &mut Container = unsafe { &mut *(c as *mut Container) };
    container.logError("Function is not implemented.");
    fmi2Error
}

macro_rules! get_container {
    ($c:expr) => {{
        if $c.is_null() {
            eprintln!("Argument c must not be NULL.");
            return fmi2Error;
        }
        unsafe { &mut *($c as *mut Container) }
    }};
}

/* Inquire version numbers and setting logging status */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetVersion() -> fmi2String {
    b"2.0\0".as_ptr() as fmi2String
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetTypesPlatform() -> fmi2String {
    b"default\0".as_ptr() as fmi2String
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetDebugLogging(
    c: fmi2Component,
    loggingOn: fmi2Boolean,
    nCategories: usize,
    categories: *const fmi2String,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

/* Creation and destruction of FMU instances */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2Instantiate(
    instanceName: fmi2String,
    fmuType: fmi2Type,
    fmuGUID: fmi2String,
    fmuResourceLocation: fmi2String,
    functions: *const fmi2CallbackFunctions,
    visible: fmi2Boolean,
    loggingOn: fmi2Boolean,
) -> fmi2Component {
    let resource_path = unsafe { CStr::from_ptr(fmuResourceLocation) };
    let s = resource_path.to_str().unwrap();
    let url = Url::parse(s).unwrap();
    let res_path = url.to_file_path().unwrap();

    let componentEnvironment = unsafe { (*functions).componentEnvironment };
    let logger = unsafe { (*functions).logger };
    let instanceName = unsafe { CStr::from_ptr(instanceName) }.to_owned();

    let log_error = |message: &str| {
        let message = CString::new(message).unwrap();
        unsafe {
            logger(
                componentEnvironment,
                instanceName.as_ptr() as fmi2String,
                fmi2Error,
                LOG_STATUS_ERROR,
                message.as_ptr(),
            )
        };
    };

    if fmuGUID.is_null() {
        log_error("Argument fmuGUID must not be NULL.");
        return null_mut();
    }

    let instantiation_token = unsafe { CStr::from_ptr(fmuGUID) };
    let instantiation_token = instantiation_token.to_string_lossy().into_owned();

    let instance_name: CString = instanceName.clone();

    // Convert raw pointer to thread-safe representation
    let component_env_ptr = componentEnvironment as usize;
    let instance_name_clone = instanceName.clone();

    let log_message = move |status: &fmiStatus, category: &str, message: &str| {
        let message = CString::new(message).unwrap();
        unsafe {
            logger(
                component_env_ptr as *mut std::os::raw::c_void,
                instance_name_clone.as_ptr(),
                *status,
                LOG_FMI_CALLS,
                message.as_ptr(),
            )
        };
    };

    let instance_name_clone2 = instanceName.clone();

    let log_fmi_call = move |status: &fmiStatus, component: &str, message: &str| {
        let message = format!("[{component}] {message}");
        let message = CString::new(message).unwrap();
        unsafe {
            logger(
                component_env_ptr as *mut std::os::raw::c_void,
                instance_name_clone2.as_ptr(),
                *status,
                LOG_FMI_CALLS,
                message.as_ptr(),
            )
        };
    };

    match Container::instantiate(
        &instantiation_token,
        &res_path,
        Arc::new(log_message),
        Arc::new(log_fmi_call),
        loggingOn != fmi2False,
        visible != fmi2False,
        componentEnvironment,
    ) {
        Ok(container) => {
            let container = Box::new(container);
            Box::into_raw(container) as fmi2Component
        }
        Err(error) => {
            log_error(&error);
            null_mut()
        }
    }
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2FreeInstance(c: fmi2Component) {
    if c.is_null() {
        return;
    }

    unsafe {
        let _ = Box::from_raw(c as *mut Container);
        // Box is dropped here, memory is freed
    }
}

/* Enter and exit initialization mode, terminate and reset */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetupExperiment(
    c: fmi2Component,
    toleranceDefined: fmi2Boolean,
    tolerance: fmi2Real,
    startTime: fmi2Real,
    stopTimeDefined: fmi2Boolean,
    stopTime: fmi2Real,
) -> fmi2Status {
    let container = get_container!(c);
    if toleranceDefined != fmi2False {
        container.tolerance = Some(tolerance);
    }
    container.startTime = startTime;
    if stopTimeDefined != fmi2False {
        container.stopTime = Some(stopTime);
    }
    fmi2OK
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2EnterInitializationMode(c: fmi2Component) -> fmi2Status {
    let container = get_container!(c);
    container.enterInitializationMode()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2ExitInitializationMode(c: fmi2Component) -> fmi2Status {
    get_container!(c).exitInitializationMode()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2Terminate(c: fmi2Component) -> fmi2Status {
    get_container!(c).terminate()
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2Reset(c: fmi2Component) -> fmi2Status {
    get_container!(c).reset()
}

/* Getting and setting variable values */

macro_rules! get_variable {
    ($c:ident, $vr:ident, $nvr:ident, $value:ident, $getter:ident) => {{
        if $c.is_null() {
            eprintln!("Argument c must not be NULL.");
            return fmi2Error;
        }

        let container = unsafe { &mut *($c as *mut Container) };

        if $vr.is_null() {
            container.logError("Argument vr must not be NULL.");
            return fmi2Error;
        }

        if $value.is_null() {
            container.logError("Argument value must not be NULL.");
            return fmi2Error;
        }

        let valueReferences = unsafe { std::slice::from_raw_parts($vr, $nvr) };
        let values = unsafe { std::slice::from_raw_parts_mut($value, $nvr) };

        container.$getter(valueReferences, values)
    }};
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetReal(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Real,
) -> fmi2Status {
    get_variable!(c, vr, nvr, value, getFloat64)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetInteger(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Integer,
) -> fmi2Status {
    get_variable!(c, vr, nvr, value, getInt32)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetBoolean(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Boolean,
) -> fmi2Status {
    if c.is_null() {
        eprintln!("Argument c must not be NULL.");
        return fmi2Error;
    }

    let container = unsafe { &mut *(c as *mut Container) };

    if vr.is_null() {
        container.logError("Argument vr must not be NULL.");
        return fmi2Error;
    }

    if value.is_null() {
        container.logError("Argument value must not be NULL.");
        return fmi2Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let value = unsafe { std::slice::from_raw_parts_mut(value, nvr) };

    let mut buffer = vec![false; nvr];

    let status = container.getBoolean(valueReferences, &mut buffer);

    for (i, v) in buffer.iter().enumerate() {
        value[i] = if *v { fmi2True } else { fmi2False };
    }

    status
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetString(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2String,
) -> fmi2Status {
    if c.is_null() {
        eprintln!("Argument c must not be NULL.");
        return fmi2Error;
    }

    let container = unsafe { &mut *(c as *mut Container) };

    if vr.is_null() {
        container.logError("Argument vr must not be NULL.");
        return fmi2Error;
    }

    if value.is_null() {
        container.logError("Argument value must not be NULL.");
        return fmi2Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts_mut(value, nvr) };

    let mut buffer: Vec<String> = vec![String::new(); values.len()];

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

macro_rules! set_variable {
    ($c:ident, $vr:ident, $nvr:ident, $value:ident, $setter:ident) => {{
        if $c.is_null() {
            eprintln!("Argument c must not be NULL.");
            return fmi2Error;
        }

        let container = unsafe { &mut *($c as *mut Container) };

        if $vr.is_null() {
            container.logError("Argument vr must not be NULL.");
            return fmi2Error;
        }

        if $value.is_null() {
            container.logError("Argument value must not be NULL.");
            return fmi2Error;
        }

        let valueReferences = unsafe { std::slice::from_raw_parts($vr, $nvr) };
        let values = unsafe { std::slice::from_raw_parts($value, $nvr) };

        container.$setter(valueReferences, values)
    }};
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetReal(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Real,
) -> fmi2Status {
    set_variable!(c, vr, nvr, value, setFloat64)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetInteger(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Integer,
) -> fmi2Status {
    set_variable!(c, vr, nvr, value, setInt32)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetBoolean(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Boolean,
) -> fmi2Status {
    if c.is_null() {
        eprintln!("Argument c must not be NULL.");
        return fmi2Error;
    }

    let container = unsafe { &mut *(c as *mut Container) };

    if vr.is_null() {
        container.logError("Argument vr must not be NULL.");
        return fmi2Error;
    }

    if value.is_null() {
        container.logError("Argument value must not be NULL.");
        return fmi2Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts(value, nvr) };

    let values: Vec<fmiBoolean> = values.iter().map(|&v| v != fmi2False).collect();

    container.setBoolean(valueReferences, &values)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetString(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2String,
) -> fmi2Status {
    if c.is_null() {
        eprintln!("Argument c must not be NULL.");
        return fmi2Error;
    }

    let container = unsafe { &mut *(c as *mut Container) };

    if vr.is_null() {
        container.logError("Argument vr must not be NULL.");
        return fmi2Error;
    }

    if value.is_null() {
        container.logError("Argument value must not be NULL.");
        return fmi2Error;
    }

    let valueReferences = unsafe { std::slice::from_raw_parts(vr, nvr) };
    let values = unsafe { std::slice::from_raw_parts(value, nvr) };

    let values: Vec<String> = values
        .iter()
        .map(|&v| unsafe { CStr::from_ptr(v).to_string_lossy().into_owned() })
        .collect();

    let v: Vec<&str> = values.iter().map(|v| v.as_str()).collect();

    container.setString(valueReferences, &v)
}

/* Getting and setting the internal FMU state */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetFMUstate(c: fmi2Component, FMUstate: *mut fmi2FMUstate) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetFMUstate(c: fmi2Component, FMUstate: fmi2FMUstate) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2FreeFMUstate(c: fmi2Component, FMUstate: *mut fmi2FMUstate) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SerializedFMUstateSize(
    c: fmi2Component,
    FMUstate: fmi2FMUstate,
    size: *mut usize,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SerializeFMUstate(
    c: fmi2Component,
    FMUstate: fmi2FMUstate,
    serializedState: *mut fmi2Byte,
    size: usize,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2DeSerializeFMUstate(
    c: fmi2Component,
    serializedState: *const fmi2Byte,
    size: usize,
    FMUstate: *mut fmi2FMUstate,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

/* Getting partial derivatives */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetDirectionalDerivative(
    c: fmi2Component,
    vUnknown_ref: *const fmi2ValueReference,
    nUnknown: usize,
    vKnown_ref: *const fmi2ValueReference,
    nKnown: usize,
    dvKnown: *const fmi2Real,
    dvUnknown: *mut fmi2Real,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

/* Co-Simulation specific functions */

#[unsafe(no_mangle)]
pub extern "C" fn fmi2SetRealInputDerivatives(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    order: *const fmi2Integer,
    value: *const fmi2Real,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetRealOutputDerivatives(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    order: *const fmi2Integer,
    value: *mut fmi2Real,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2DoStep(
    c: fmi2Component,
    currentCommunicationPoint: fmi2Real,
    communicationStepSize: fmi2Real,
    noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
) -> fmi2Status {
    let container = get_container!(c);
    container.doStep(currentCommunicationPoint, communicationStepSize)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2CancelStep(c: fmi2Component) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetStatus(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Status,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetRealStatus(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Real,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetIntegerStatus(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Integer,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetBooleanStatus(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Boolean,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}

#[unsafe(no_mangle)]
pub extern "C" fn fmi2GetStringStatus(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2String,
) -> fmi2Status {
    NOT_IMPLEMENTED(c)
}
