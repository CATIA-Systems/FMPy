#![allow(non_camel_case_types, non_snake_case, dead_code)]

pub mod types;

use libloading::{Library, Symbol};
use std::error::Error;
use std::ffi::{CStr, CString};
use std::os::raw::c_void;
use std::path::Path;
use std::ptr::null;
use std::ptr::{self, null_mut};
use std::sync::Arc;
use types::*;
use url::Url;

use crate::{SHARED_LIBRARY_EXTENSION, types::*};

#[cfg(all(target_arch = "aarch64", target_os = "linux"))]
pub const PLATFORM: &str = "aarch64-linux";

#[cfg(all(target_arch = "x86_64", target_os = "linux"))]
pub const PLATFORM: &str = "linux64";

#[cfg(all(target_arch = "aarch64", target_os = "macos"))]
pub const PLATFORM: &str = "aarch64-darwin";

#[cfg(all(target_arch = "x86_64", target_os = "macos"))]
pub const PLATFORM: &str = "darwin64";

#[cfg(all(target_arch = "x86", target_os = "windows"))]
pub const PLATFORM: &str = "win32";

#[cfg(all(target_arch = "x86_64", target_os = "windows"))]
pub const PLATFORM: &str = "win64";

/// Macro to check FMI status and return early if error or fatal
/// Usage: fmi_check_status!(status);
#[macro_export]
macro_rules! fmi2_check_status {
    ($status:expr) => {{
        let __fmi_status = $status;
        if __fmi_status > fmi2Warning {
            return __fmi_status;
        }
    }};
}

macro_rules! fmi2_get {
    ($self:expr, $func:ident, $value_refs:expr, $values:expr) => {{
        debug_assert_eq!($value_refs.len(), $values.len());

        let status = unsafe {
            ($self.$func)(
                $self.component,
                $value_refs.as_ptr(),
                $value_refs.len(),
                $values.as_mut_ptr(),
            )
        };

        if let Some(cb) = &$self.logFMICall {
            let message = format!(
                "{}(valueReferences={:?}, nvr={}, values={:?}) -> {:?}",
                stringify!($func),
                $value_refs,
                $value_refs.len(),
                $values,
                status
            );
            cb(&status, message.as_str());
        }

        status
    }};
}

macro_rules! fmi2_set {
    ($self:expr, $func:ident, $value_refs:expr, $values:expr) => {{
        debug_assert_eq!(
            $value_refs.len(),
            $values.len(),
            "The number of values must be equal to the number of values references."
        );

        let status = unsafe {
            ($self.$func)(
                $self.component,
                $value_refs.as_ptr(),
                $value_refs.len(),
                $values.as_ptr(),
            )
        };

        if let Some(cb) = &$self.logFMICall {
            let message = format!(
                "{}(valueReferences={:?}, nvr={}, values={:?})",
                stringify!($func),
                $value_refs,
                $value_refs.len(),
                $values
            );
            cb(&status, message.as_str());
        }

        status
    }};
}

impl<'lib> Drop for FMU2<'lib> {
    fn drop(&mut self) {
        if !self.component.is_null() {
            unsafe { (self.fmi2FreeInstance)(self.component) };
            self.component = null_mut();
            if let Some(cb) = &self.logFMICall {
                cb(&fmi2OK, "fmi2FreeInstance()");
            }
        }
    }
}

pub struct FMU2<'lib> {
    instanceName: String,

    logFMICall: Option<Arc<LogFMICallCallback>>,
    logMessage: Option<Arc<LogMessageCallback>>,

    _lib: Box<Library>,

    fmi2GetVersion: Symbol<'lib, fmi2GetVersionTYPE>,
    fmi2GetTypesPlatform: Symbol<'lib, fmi2GetTypesPlatformTYPE>,
    fmi2SetDebugLogging: Symbol<'lib, fmi2SetDebugLoggingTYPE>,
    fmi2Instantiate: Symbol<'lib, fmi2InstantiateTYPE>,
    fmi2FreeInstance: Symbol<'lib, fmi2FreeInstanceTYPE>,
    fmi2SetupExperiment: Symbol<'lib, fmi2SetupExperimentTYPE>,
    fmi2EnterInitializationMode: Symbol<'lib, fmi2EnterInitializationModeTYPE>,
    fmi2ExitInitializationMode: Symbol<'lib, fmi2ExitInitializationModeTYPE>,
    fmi2Terminate: Symbol<'lib, fmi2TerminateTYPE>,
    fmi2Reset: Symbol<'lib, fmi2ResetTYPE>,
    fmi2GetReal: Symbol<'lib, fmi2GetRealTYPE>,
    fmi2GetInteger: Symbol<'lib, fmi2GetIntegerTYPE>,
    fmi2GetBoolean: Symbol<'lib, fmi2GetBooleanTYPE>,
    fmi2GetString: Symbol<'lib, fmi2GetStringTYPE>,
    fmi2SetReal: Symbol<'lib, fmi2SetRealTYPE>,
    fmi2SetInteger: Symbol<'lib, fmi2SetIntegerTYPE>,
    fmi2SetBoolean: Symbol<'lib, fmi2SetBooleanTYPE>,
    fmi2SetString: Symbol<'lib, fmi2SetStringTYPE>,
    fmi2GetFMUstate: Symbol<'lib, fmi2GetFMUstateTYPE>,
    fmi2SetFMUstate: Symbol<'lib, fmi2SetFMUstateTYPE>,
    fmi2FreeFMUstate: Symbol<'lib, fmi2FreeFMUstateTYPE>,
    fmi2SerializedFMUstateSize: Symbol<'lib, fmi2SerializedFMUstateSizeTYPE>,
    fmi2SerializeFMUstate: Symbol<'lib, fmi2SerializeFMUstateTYPE>,
    fmi2DeSerializeFMUstate: Symbol<'lib, fmi2DeSerializeFMUstateTYPE>,
    fmi2GetDirectionalDerivative: Symbol<'lib, fmi2GetDirectionalDerivativeTYPE>,

    // Model Exchange specific
    fmi2EnterEventMode: Option<Symbol<'lib, fmi2EnterEventModeTYPE>>,
    fmi2NewDiscreteStates: Option<Symbol<'lib, fmi2NewDiscreteStatesTYPE>>,
    fmi2EnterContinuousTimeMode: Option<Symbol<'lib, fmi2EnterContinuousTimeModeTYPE>>,
    fmi2CompletedIntegratorStep: Option<Symbol<'lib, fmi2CompletedIntegratorStepTYPE>>,
    fmi2SetTime: Option<Symbol<'lib, fmi2SetTimeTYPE>>,
    fmi2SetContinuousStates: Option<Symbol<'lib, fmi2SetContinuousStatesTYPE>>,
    fmi2GetDerivatives: Option<Symbol<'lib, fmi2GetDerivativesTYPE>>,
    fmi2GetEventIndicators: Option<Symbol<'lib, fmi2GetEventIndicatorsTYPE>>,
    fmi2GetContinuousStates: Option<Symbol<'lib, fmi2GetContinuousStatesTYPE>>,
    fmi2GetNominalsOfContinuousStates: Option<Symbol<'lib, fmi2GetNominalsOfContinuousStatesTYPE>>,

    // Co-Simulation specific
    fmi2SetRealInputDerivatives: Option<Symbol<'lib, fmi2SetRealInputDerivativesTYPE>>,
    fmi2GetRealOutputDerivatives: Option<Symbol<'lib, fmi2GetRealOutputDerivativesTYPE>>,
    fmi2DoStep: Option<Symbol<'lib, fmi2DoStepTYPE>>,
    fmi2CancelStep: Option<Symbol<'lib, fmi2CancelStepTYPE>>,
    fmi2GetStatus: Option<Symbol<'lib, fmi2GetStatusTYPE>>,
    fmi2GetRealStatus: Option<Symbol<'lib, fmi2GetRealStatusTYPE>>,
    fmi2GetIntegerStatus: Option<Symbol<'lib, fmi2GetIntegerStatusTYPE>>,
    fmi2GetBooleanStatus: Option<Symbol<'lib, fmi2GetBooleanStatusTYPE>>,
    fmi2GetStringStatus: Option<Symbol<'lib, fmi2GetStringStatusTYPE>>,

    component: fmi2Component,
}

#[unsafe(no_mangle)]
pub extern "C" fn logMessage2(
    componentEnvironment: fmi2ComponentEnvironment,
    _instanceName: fmi2String,
    status: fmi2Status,
    category: fmi2String,
    message: fmi2String,
) {
    if componentEnvironment.is_null() {
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
        let cb_ptr = componentEnvironment as *mut Arc<LogMessageCallback>;
        let cb: &Arc<LogMessageCallback> = &*cb_ptr;
        cb(&status, &category_str, &message_str);
    }
}

fn get_symbol<'lib, T>(lib: &Library, symbol_name: &[u8]) -> Result<Symbol<'lib, T>, String> {
    unsafe {
        let symbol: Result<Symbol<T>, libloading::Error> = lib.get(symbol_name);
        match symbol {
            Ok(s) => Ok(std::mem::transmute(s)),
            Err(error) => {
                let message = format!("Failed to load {symbol_name:?}. {error:?}");
                Err(message)
            }
        }
    }
}

fn try_get_symbol<'lib, T>(lib: &Library, symbol_name: &[u8]) -> Option<Symbol<'lib, T>> {
    unsafe {
        if let Ok(symbol) = lib.get::<T>(symbol_name) {
            Some(std::mem::transmute(symbol))
        } else {
            None
        }
    }
}

impl<'lib> FMU2<'lib> {
    pub fn new(
        unzipdir: &Path,
        modelIdentifier: &str,
        instanceName: &str,
        interfaceType: fmi2Type,
        guid: &str,
        visible: bool,
        loggingOn: bool,
        logFMICall: Option<Box<LogFMICallCallback>>,
        logMessage: Option<Box<LogMessageCallback>>,
    ) -> Result<FMU2<'lib>, Box<dyn Error>> {

        let shared_library_path = unzipdir
            .join("binaries")
            .join(PLATFORM)
            .join(format!("{modelIdentifier}{SHARED_LIBRARY_EXTENSION}"));

        if !shared_library_path.is_file() {
            return Err(format!("Missing shared library {shared_library_path:?}.").into())
        }

        let lib = Box::new(unsafe { Library::new(shared_library_path)? });

        // Load all symbols using the generic get_symbol function
        let fmi2GetVersion = get_symbol::<fmi2GetVersionTYPE>(&lib, b"fmi2GetVersion")?;
        let fmi2GetTypesPlatform =
            get_symbol::<fmi2GetTypesPlatformTYPE>(&lib, b"fmi2GetTypesPlatform")?;
        let fmi2SetDebugLogging =
            get_symbol::<fmi2SetDebugLoggingTYPE>(&lib, b"fmi2SetDebugLogging")?;
        let fmi2Instantiate = get_symbol::<fmi2InstantiateTYPE>(&lib, b"fmi2Instantiate")?;
        let fmi2FreeInstance = get_symbol::<fmi2FreeInstanceTYPE>(&lib, b"fmi2FreeInstance")?;
        let fmi2SetupExperiment =
            get_symbol::<fmi2SetupExperimentTYPE>(&lib, b"fmi2SetupExperiment")?;
        let fmi2EnterInitializationMode =
            get_symbol::<fmi2EnterInitializationModeTYPE>(&lib, b"fmi2EnterInitializationMode")?;
        let fmi2ExitInitializationMode =
            get_symbol::<fmi2ExitInitializationModeTYPE>(&lib, b"fmi2ExitInitializationMode")?;
        let fmi2Terminate = get_symbol::<fmi2TerminateTYPE>(&lib, b"fmi2Terminate")?;
        let fmi2Reset = get_symbol::<fmi2ResetTYPE>(&lib, b"fmi2Reset")?;
        let fmi2GetReal = get_symbol::<fmi2GetRealTYPE>(&lib, b"fmi2GetReal")?;
        let fmi2GetInteger = get_symbol::<fmi2GetIntegerTYPE>(&lib, b"fmi2GetInteger")?;
        let fmi2GetBoolean = get_symbol::<fmi2GetBooleanTYPE>(&lib, b"fmi2GetBoolean")?;
        let fmi2GetString = get_symbol::<fmi2GetStringTYPE>(&lib, b"fmi2GetString")?;
        let fmi2SetReal = get_symbol::<fmi2SetRealTYPE>(&lib, b"fmi2SetReal")?;
        let fmi2SetInteger = get_symbol::<fmi2SetIntegerTYPE>(&lib, b"fmi2SetInteger")?;
        let fmi2SetBoolean = get_symbol::<fmi2SetBooleanTYPE>(&lib, b"fmi2SetBoolean")?;
        let fmi2SetString = get_symbol::<fmi2SetStringTYPE>(&lib, b"fmi2SetString")?;
        let fmi2GetFMUstate = get_symbol::<fmi2GetFMUstateTYPE>(&lib, b"fmi2GetFMUstate")?;
        let fmi2SetFMUstate = get_symbol::<fmi2SetFMUstateTYPE>(&lib, b"fmi2SetFMUstate")?;
        let fmi2FreeFMUstate = get_symbol::<fmi2FreeFMUstateTYPE>(&lib, b"fmi2FreeFMUstate")?;
        let fmi2SerializedFMUstateSize =
            get_symbol::<fmi2SerializedFMUstateSizeTYPE>(&lib, b"fmi2SerializedFMUstateSize")?;
        let fmi2SerializeFMUstate =
            get_symbol::<fmi2SerializeFMUstateTYPE>(&lib, b"fmi2SerializeFMUstate")?;
        let fmi2DeSerializeFMUstate =
            get_symbol::<fmi2DeSerializeFMUstateTYPE>(&lib, b"fmi2DeSerializeFMUstate")?;
        let fmi2GetDirectionalDerivative =
            get_symbol::<fmi2GetDirectionalDerivativeTYPE>(&lib, b"fmi2GetDirectionalDerivative")?;

        // Model Exchange specific
        let fmi2EnterEventMode =
            try_get_symbol::<fmi2EnterEventModeTYPE>(&lib, b"fmi2EnterEventMode");

        let fmi2NewDiscreteStates =
            try_get_symbol::<fmi2NewDiscreteStatesTYPE>(&lib, b"fmi2NewDiscreteStates");

        let fmi2EnterContinuousTimeMode =
            try_get_symbol::<fmi2EnterContinuousTimeModeTYPE>(&lib, b"fmi2EnterContinuousTimeMode");

        let fmi2CompletedIntegratorStep =
            try_get_symbol::<fmi2CompletedIntegratorStepTYPE>(&lib, b"fmi2CompletedIntegratorStep");

        let fmi2SetTime = try_get_symbol::<fmi2SetTimeTYPE>(&lib, b"fmi2SetTime");

        let fmi2SetContinuousStates =
            try_get_symbol::<fmi2SetContinuousStatesTYPE>(&lib, b"fmi2SetContinuousStates");

        let fmi2GetDerivatives =
            try_get_symbol::<fmi2GetDerivativesTYPE>(&lib, b"fmi2GetDerivatives");

        let fmi2GetEventIndicators =
            try_get_symbol::<fmi2GetEventIndicatorsTYPE>(&lib, b"fmi2GetEventIndicators");

        let fmi2GetContinuousStates =
            try_get_symbol::<fmi2GetContinuousStatesTYPE>(&lib, b"fmi2GetContinuousStates");

        let fmi2GetNominalsOfContinuousStates = try_get_symbol::<
            fmi2GetNominalsOfContinuousStatesTYPE,
        >(
            &lib, b"fmi2GetNominalsOfContinuousStates"
        );

        // Co-Simulation specific
        let fmi2SetRealInputDerivatives =
            try_get_symbol::<fmi2SetRealInputDerivativesTYPE>(&lib, b"fmi2SetRealInputDerivatives");

        let fmi2GetRealOutputDerivatives = try_get_symbol::<fmi2GetRealOutputDerivativesTYPE>(
            &lib,
            b"fmi2GetRealOutputDerivatives",
        );

        let fmi2DoStep = try_get_symbol::<fmi2DoStepTYPE>(&lib, b"fmi2DoStep");

        let fmi2CancelStep = try_get_symbol::<fmi2CancelStepTYPE>(&lib, b"fmi2CancelStep");

        let fmi2GetStatus = try_get_symbol::<fmi2GetStatusTYPE>(&lib, b"fmi2GetStatus");

        let fmi2GetRealStatus = try_get_symbol::<fmi2GetRealStatusTYPE>(&lib, b"fmi2GetRealStatus");

        let fmi2GetIntegerStatus =
            try_get_symbol::<fmi2GetIntegerStatusTYPE>(&lib, b"fmi2GetIntegerStatus");

        let fmi2GetBooleanStatus =
            try_get_symbol::<fmi2GetBooleanStatusTYPE>(&lib, b"fmi2GetBooleanStatus");

        let fmi2GetStringStatus =
            try_get_symbol::<fmi2GetStringStatusTYPE>(&lib, b"fmi2GetStringStatus");

        let mut fmu = FMU2 {
            instanceName: String::from(instanceName),
            logFMICall: logFMICall.map(|cb| Arc::from(cb)),
            logMessage: logMessage.map(|cb| Arc::from(cb)),
            _lib: lib,
            fmi2GetVersion,
            fmi2GetTypesPlatform,
            fmi2SetDebugLogging,
            fmi2Instantiate,
            fmi2FreeInstance,
            fmi2SetupExperiment,
            fmi2EnterInitializationMode,
            fmi2ExitInitializationMode,
            fmi2Terminate,
            fmi2Reset,
            fmi2GetReal,
            fmi2GetInteger,
            fmi2GetBoolean,
            fmi2GetString,
            fmi2SetReal,
            fmi2SetInteger,
            fmi2SetBoolean,
            fmi2SetString,
            fmi2GetFMUstate,
            fmi2SetFMUstate,
            fmi2FreeFMUstate,
            fmi2SerializedFMUstateSize,
            fmi2SerializeFMUstate,
            fmi2DeSerializeFMUstate,
            fmi2GetDirectionalDerivative,
            fmi2EnterEventMode,
            fmi2NewDiscreteStates,
            fmi2EnterContinuousTimeMode,
            fmi2CompletedIntegratorStep,
            fmi2SetTime,
            fmi2SetContinuousStates,
            fmi2GetDerivatives,
            fmi2GetEventIndicators,
            fmi2GetContinuousStates,
            fmi2GetNominalsOfContinuousStates,
            fmi2SetRealInputDerivatives,
            fmi2GetRealOutputDerivatives,
            fmi2DoStep,
            fmi2CancelStep,
            fmi2GetStatus,
            fmi2GetRealStatus,
            fmi2GetIntegerStatus,
            fmi2GetBooleanStatus,
            fmi2GetStringStatus,
            component: ptr::null_mut(),
        };

        let resource_path = unzipdir.join("resources").join("");

        let resourceUrl = if resource_path.is_dir() {
            Url::from_directory_path(resource_path).ok()
        } else {
            None
        };

        fmu.component = fmu.instantiate(instanceName, interfaceType, guid, resourceUrl.as_ref(), visible, loggingOn);
        
        if fmu.component.is_null() {
            Err("Failed to instantiate FMU.".into())
        } else {
            Ok(fmu)
        }
    }

    pub fn getVersion(&self) -> String {
        let version = unsafe {
            let version_cstr = (self.fmi2GetVersion)();
            CStr::from_ptr(version_cstr).to_string_lossy().into_owned()
        };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi2GetVersion() -> \"{version}\"");
            cb(&fmi2OK, message.as_str());
        }
        version
    }

    pub fn getTypesPlatform(&self) -> String {
        let types_platform = unsafe {
            let platform_cstr = (self.fmi2GetTypesPlatform)();
            CStr::from_ptr(platform_cstr).to_string_lossy().into_owned()
        };
        if let Some(cb) = &self.logFMICall {
            let message = format!("fmi2GetTypesPlatform() -> {types_platform}");
            cb(&fmi2OK, message.as_str());
        }
        types_platform
    }

    fn instantiate(
        &mut self,
        instanceName: &str,
        interfaceType: fmi2Type,
        guid: &str,
        resourceUrl: Option<&Url>,
        visible: bool,
        loggingOn: bool,
    ) -> fmi2Component {
        let instance_name_cstr = CString::new(instanceName).unwrap();
        let fmu_guid_cstr = CString::new(guid).unwrap();

        let url_cstr;

        let fmuResourceLocation = if let Some(url) = resourceUrl {
            url_cstr = CString::new(url.to_string()).unwrap();
            url_cstr.as_ptr() as fmi2String
        } else {
            null() as fmi2String
        };

        // Create callback functions structure
        let userdata = if let Some(callback) = self.logMessage.take() {
            Box::into_raw(Box::new(callback)) as *mut c_void
        } else {
            ptr::null_mut()
        };

        // Simple memory allocation functions for FMI 2.0
        unsafe extern "C" fn allocate_memory(nobj: usize, size: usize) -> *mut c_void {
            unsafe {
                let layout = std::alloc::Layout::from_size_align_unchecked(nobj * size, 1);
                std::alloc::alloc(layout) as *mut c_void
            }
        }

        unsafe extern "C" fn free_memory(obj: *mut c_void) {
            if !obj.is_null() {
                unsafe {
                    std::alloc::dealloc(
                        obj as *mut u8,
                        std::alloc::Layout::from_size_align_unchecked(1, 1),
                    );
                }
            }
        }

        unsafe extern "C" fn step_finished(_env: fmi2ComponentEnvironment, _status: fmi2Status) {
            // default implementation - do nothing
        }

        let callbacks = fmi2CallbackFunctions {
            logger: logMessage2,
            allocateMemory: allocate_memory,
            freeMemory: free_memory,
            stepFinished: step_finished,
            componentEnvironment: userdata,
        };

        let component = unsafe {
            (self.fmi2Instantiate)(
                instance_name_cstr.as_ptr(),
                interfaceType,
                fmu_guid_cstr.as_ptr(),
                fmuResourceLocation,
                &callbacks,
                if visible { fmi2True } else { fmi2False },
                if loggingOn { fmi2True } else { fmi2False },
            )
        };

        if let Some(cb) = &self.logFMICall {
            let url = if let Some(url) = resourceUrl {
                url.to_string()
            } else {
                String::from("None")
            };

            let message = format!(
                "fmi2Instantiate(instanceName=\"{}\", fmuType={:?}, fmuGUID=\"{}\", fmuResourceLocation={:?}, visible={}, loggingOn={})",
                instanceName, interfaceType, guid, url, visible, loggingOn
            );

            if component.is_null() {
                cb(&fmi2Error, &message);
            } else {
                cb(&fmi2OK, &message);
            }
        }

        component
    }

    pub fn terminate(&self) -> fmi2Status {
        let status = unsafe { (self.fmi2Terminate)(self.component) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2Terminate()");
        }
        status
    }

    pub fn setupExperiment(
        &self,
        tolerance: Option<fmi2Real>,
        startTime: fmi2Real,
        stopTime: Option<fmi2Real>,
    ) -> fmi2Status {
        let (toleranceDefined, tolerance) = if let Some(tolerance) = tolerance {
            (fmi2True, tolerance)
        } else {
            (fmi2False, 0.0)
        };

        let (stopTimeDefined, stopTime) = if let Some(stopTime) = stopTime {
            (fmi2True, stopTime)
        } else {
            (fmi2False, 0.0)
        };

        let status = unsafe {
            (self.fmi2SetupExperiment)(
                self.component,
                toleranceDefined,
                tolerance,
                startTime,
                stopTimeDefined,
                stopTime,
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi2SetupExperiment(toleranceDefined={}, tolerance={}, startTime={}, stopTimeDefined={}, stopTime={})",
                toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime
            );
            cb(&status, message.as_str());
        }

        status
    }

    pub fn enterInitializationMode(&self) -> fmi2Status {
        let status = unsafe { (self.fmi2EnterInitializationMode)(self.component) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2EnterInitializationMode()");
        }
        status
    }

    pub fn exitInitializationMode(&self) -> fmi2Status {
        let status = unsafe { (self.fmi2ExitInitializationMode)(self.component) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2ExitInitializationMode()");
        }
        status
    }

    pub fn reset(&self) -> fmi2Status {
        let status = unsafe { (self.fmi2Reset)(self.component) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2Reset()");
        }
        status
    }

    fn freeInstance(&mut self) {
        unsafe { (self.fmi2FreeInstance)(self.component) };
        self.component = null_mut();
        if let Some(cb) = &self.logFMICall {
            cb(&fmi2OK, "fmi2FreeInstance()");
        }
    }

    // Variable access methods
    pub fn getReal(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &mut [fmi2Real],
    ) -> fmi2Status {
        fmi2_get!(self, fmi2GetReal, valueReferences, values)
    }

    pub fn getInteger(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &mut [fmi2Integer],
    ) -> fmi2Status {
        fmi2_get!(self, fmi2GetInteger, valueReferences, values)
    }

    pub fn getBoolean(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &mut [fmi2Boolean],
    ) -> fmi2Status {
        fmi2_get!(self, fmi2GetBoolean, valueReferences, values)
    }

    pub fn getString(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &mut [String],
    ) -> fmi2Status {
        debug_assert_eq!(valueReferences.len(), values.len());

        let mut buffer: Vec<fmi2String> = vec![null(); values.len()];

        let status = unsafe {
            (self.fmi2GetString)(
                self.component,
                valueReferences.as_ptr(),
                valueReferences.len(),
                buffer.as_mut_ptr(),
            )
        };

        for (i, v) in buffer.iter().enumerate() {
            values[i] = unsafe { CStr::from_ptr(*v).to_string_lossy().into_owned() };
        }

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi2GetString(valueReferences={:?}, nvr={}, values={:?}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                values,
                status
            );
            cb(&status, message.as_str());
        }

        status
    }

    pub fn setReal(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &[fmi2Real],
    ) -> fmi2Status {
        fmi2_set!(self, fmi2SetReal, valueReferences, values)
    }

    pub fn setInteger(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &[fmi2Integer],
    ) -> fmi2Status {
        fmi2_set!(self, fmi2SetInteger, valueReferences, values)
    }

    pub fn setBoolean(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &[fmi2Boolean],
    ) -> fmi2Status {
        fmi2_set!(self, fmi2SetBoolean, valueReferences, values)
    }

    pub fn setString(
        &self,
        valueReferences: &[fmi2ValueReference],
        values: &[&str],
    ) -> fmi2Status {
        debug_assert_eq!(valueReferences.len(), values.len());

        let values: Vec<CString> = values
                .iter()
                .map(|&v| CString::new(v).unwrap())
                .collect();

        let values2: Vec<fmi2String> = values.iter().map(|v| v.as_ptr() as fmi2String).collect();

        let status = unsafe {
            (self.fmi2SetString)(
                self.component,
                valueReferences.as_ptr(),
                valueReferences.len(),
                values2.as_ptr(),
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi2SetString(valueReferences={:?}, nvr={}, values={:?}) -> {:?}",
                valueReferences,
                valueReferences.len(),
                values,
                status
            );
            cb(&status, message.as_str());
        }

        status
    }

    // Co-Simulation specific methods
    pub fn doStep(
        &self,
        currentCommunicationPoint: fmi2Real,
        communicationStepSize: fmi2Real,
        noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
    ) -> fmi2Status {
        let status = unsafe {
            (self.fmi2DoStep.as_ref().unwrap())(
                self.component,
                currentCommunicationPoint,
                communicationStepSize,
                noSetFMUStatePriorToCurrentPoint,
            )
        };

        if let Some(cb) = &self.logFMICall {
            let message = format!(
                "fmi2DoStep(currentCommunicationPoint={}, communicationStepSize={}, noSetFMUStatePriorToCurrentPoint={})",
                currentCommunicationPoint,
                communicationStepSize,
                noSetFMUStatePriorToCurrentPoint
            );
            cb(&status, message.as_str());
        }

        status
    }

    pub fn getRealStatus(&self, s: &fmi2StatusKind, value: &mut fmi2Real) -> fmi2Status {
        let status =
            unsafe { (self.fmi2GetRealStatus.as_ref().unwrap())(self.component, *s, value) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2GetRealStatus(s={s}, value={value})");
        }
        status
    }

    pub fn getBooleanStatus(&self, s: &fmi2StatusKind, value: &mut fmi2Boolean) -> fmi2Status {
        let status =
            unsafe { (self.fmi2GetBooleanStatus.as_ref().unwrap())(self.component, *s, value) };
        if let Some(cb) = &self.logFMICall {
            cb(&status, "fmi2GetBooleanStatus(s={s}, value={value})");
        }
        status
    }

    // Model Exchange specific methods
    pub fn setTime(&self, _time: fmi2Real) -> fmi2Status {
        fmi2Fatal
        // let status = unsafe { (self.fmi2SetTime)(self.component, time) };
        // if let Some(cb) = &self.logFMICall {
        //     let message = format!("fmi2SetTime(time={}) -> {:?}", time, status);
        //     cb(&status, message.as_str());
        // }
        // status
    }

    pub fn enterEventMode(&self) -> fmi2Status {
        if let Some(f) = &self.fmi2EnterEventMode {
            let status = unsafe { (f)(self.component) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2EnterEventMode() -> {:?}", status);
                cb(&status, message.as_str());
            }
            status
        } else {
            fmi2Fatal
        }
    }

    pub fn enterContinuousTimeMode(&self) -> fmi2Status {
        fmi2Fatal
        // let status = unsafe { (self.fmi2EnterContinuousTimeMode)(self.component) };
        // if let Some(cb) = &self.logFMICall {
        //     let message = format!("fmi2EnterContinuousTimeMode() -> {:?}", status);
        //     cb(&status, message.as_str());
        // }
        // status
    }
}
// Explicitly implement Sync for FMU2 since all fields are now Sync
unsafe impl<'lib> Sync for FMU2<'lib> {}