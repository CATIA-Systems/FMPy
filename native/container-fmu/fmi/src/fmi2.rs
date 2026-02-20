#![allow(non_camel_case_types, non_snake_case, dead_code)]

pub mod types;

use libloading::{Library, Symbol};
use std::error::Error;
use std::ffi::{CStr, CString};
use std::os::raw::c_void;
use std::path::Path;
use std::ptr;
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

enum InterfaceType {
    ModelExchange(ModelExchangeFunctions),
    CoSimulation(CoSimulationFunctions),
}

struct ModelExchangeFunctions {
    fmi2EnterEventMode: Symbol<'static, fmi2EnterEventModeTYPE>,
    fmi2NewDiscreteStates: Symbol<'static, fmi2NewDiscreteStatesTYPE>,
    fmi2EnterContinuousTimeMode: Symbol<'static, fmi2EnterContinuousTimeModeTYPE>,
    fmi2CompletedIntegratorStep: Symbol<'static, fmi2CompletedIntegratorStepTYPE>,
    fmi2SetTime: Symbol<'static, fmi2SetTimeTYPE>,
    fmi2SetContinuousStates: Symbol<'static, fmi2SetContinuousStatesTYPE>,
    fmi2GetDerivatives: Symbol<'static, fmi2GetDerivativesTYPE>,
    fmi2GetEventIndicators: Symbol<'static, fmi2GetEventIndicatorsTYPE>,
    fmi2GetContinuousStates: Symbol<'static, fmi2GetContinuousStatesTYPE>,
    fmi2GetNominalsOfContinuousStates: Symbol<'static, fmi2GetNominalsOfContinuousStatesTYPE>,
}

struct CoSimulationFunctions {
    fmi2SetRealInputDerivatives: Symbol<'static, fmi2SetRealInputDerivativesTYPE>,
    fmi2GetRealOutputDerivatives: Symbol<'static, fmi2GetRealOutputDerivativesTYPE>,
    fmi2DoStep: Symbol<'static, fmi2DoStepTYPE>,
    fmi2CancelStep: Symbol<'static, fmi2CancelStepTYPE>,
    fmi2GetStatus: Symbol<'static, fmi2GetStatusTYPE>,
    fmi2GetRealStatus: Symbol<'static, fmi2GetRealStatusTYPE>,
    fmi2GetIntegerStatus: Symbol<'static, fmi2GetIntegerStatusTYPE>,
    fmi2GetBooleanStatus: Symbol<'static, fmi2GetBooleanStatusTYPE>,
    fmi2GetStringStatus: Symbol<'static, fmi2GetStringStatusTYPE>,
}

impl Drop for FMU2 {
    fn drop(&mut self) {
        if !self.component.is_null() {
            unsafe { (self.fmi2FreeInstance)(self.component) };
            if let Some(cb) = &self.logFMICall {
                cb(&fmi2OK, "fmi2FreeInstance()");
            }
        }
    }
}

pub struct FMU2 {
    instanceName: String,

    component: fmi2Component,

    logFMICall: Option<Arc<LogFMICallCallback>>,
    logMessage: Option<Arc<LogMessageCallback>>,

    _lib: Box<Library>,

    fmi2GetVersion: Symbol<'static, fmi2GetVersionTYPE>,
    fmi2GetTypesPlatform: Symbol<'static, fmi2GetTypesPlatformTYPE>,
    fmi2SetDebugLogging: Symbol<'static, fmi2SetDebugLoggingTYPE>,
    fmi2Instantiate: Symbol<'static, fmi2InstantiateTYPE>,
    fmi2FreeInstance: Symbol<'static, fmi2FreeInstanceTYPE>,
    fmi2SetupExperiment: Symbol<'static, fmi2SetupExperimentTYPE>,
    fmi2EnterInitializationMode: Symbol<'static, fmi2EnterInitializationModeTYPE>,
    fmi2ExitInitializationMode: Symbol<'static, fmi2ExitInitializationModeTYPE>,
    fmi2Terminate: Symbol<'static, fmi2TerminateTYPE>,
    fmi2Reset: Symbol<'static, fmi2ResetTYPE>,
    fmi2GetReal: Symbol<'static, fmi2GetRealTYPE>,
    fmi2GetInteger: Symbol<'static, fmi2GetIntegerTYPE>,
    fmi2GetBoolean: Symbol<'static, fmi2GetBooleanTYPE>,
    fmi2GetString: Symbol<'static, fmi2GetStringTYPE>,
    fmi2SetReal: Symbol<'static, fmi2SetRealTYPE>,
    fmi2SetInteger: Symbol<'static, fmi2SetIntegerTYPE>,
    fmi2SetBoolean: Symbol<'static, fmi2SetBooleanTYPE>,
    fmi2SetString: Symbol<'static, fmi2SetStringTYPE>,
    fmi2GetFMUstate: Symbol<'static, fmi2GetFMUstateTYPE>,
    fmi2SetFMUstate: Symbol<'static, fmi2SetFMUstateTYPE>,
    fmi2FreeFMUstate: Symbol<'static, fmi2FreeFMUstateTYPE>,
    fmi2SerializedFMUstateSize: Symbol<'static, fmi2SerializedFMUstateSizeTYPE>,
    fmi2SerializeFMUstate: Symbol<'static, fmi2SerializeFMUstateTYPE>,
    fmi2DeSerializeFMUstate: Symbol<'static, fmi2DeSerializeFMUstateTYPE>,
    fmi2GetDirectionalDerivative: Symbol<'static, fmi2GetDirectionalDerivativeTYPE>,

    interfaceType: InterfaceType,
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

fn get_symbol<T>(lib: &Library, symbol_name: &[u8]) -> Result<Symbol<'static, T>, String> {
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

impl FMU2 {
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
    ) -> Result<FMU2, Box<dyn Error>> {
        let shared_library_path = unzipdir
            .join("binaries")
            .join(PLATFORM)
            .join(format!("{modelIdentifier}{SHARED_LIBRARY_EXTENSION}"));

        if !shared_library_path.is_file() {
            return Err(format!("Missing shared library {shared_library_path:?}.").into());
        }

        let lib = Box::new(unsafe { Library::new(shared_library_path)? });

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

        let resource_path = unzipdir.join("resources").join("");

        let resourceUrl = if resource_path.is_dir() {
            Url::from_directory_path(resource_path).ok()
        } else {
            None
        };

        let interfaceType = match interfaceType {
            fmi2Type::fmi2ModelExchange => {
                let fmi2EnterEventMode =
                    get_symbol::<fmi2EnterEventModeTYPE>(&lib, b"fmi2EnterEventMode")?;
                let fmi2NewDiscreteStates =
                    get_symbol::<fmi2NewDiscreteStatesTYPE>(&lib, b"fmi2NewDiscreteStates")?;
                let fmi2EnterContinuousTimeMode = get_symbol::<fmi2EnterContinuousTimeModeTYPE>(
                    &lib,
                    b"fmi2EnterContinuousTimeMode",
                )?;
                let fmi2CompletedIntegratorStep = get_symbol::<fmi2CompletedIntegratorStepTYPE>(
                    &lib,
                    b"fmi2CompletedIntegratorStep",
                )?;
                let fmi2SetTime = get_symbol::<fmi2SetTimeTYPE>(&lib, b"fmi2SetTime")?;
                let fmi2SetContinuousStates =
                    get_symbol::<fmi2SetContinuousStatesTYPE>(&lib, b"fmi2SetContinuousStates")?;
                let fmi2GetDerivatives =
                    get_symbol::<fmi2GetDerivativesTYPE>(&lib, b"fmi2GetDerivatives")?;
                let fmi2GetEventIndicators =
                    get_symbol::<fmi2GetEventIndicatorsTYPE>(&lib, b"fmi2GetEventIndicators")?;
                let fmi2GetContinuousStates =
                    get_symbol::<fmi2GetContinuousStatesTYPE>(&lib, b"fmi2GetContinuousStates")?;
                let fmi2GetNominalsOfContinuousStates =
                    get_symbol::<fmi2GetNominalsOfContinuousStatesTYPE>(
                        &lib,
                        b"fmi2GetNominalsOfContinuousStates",
                    )?;

                let modelExchangeFunctions = ModelExchangeFunctions {
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
                };

                InterfaceType::ModelExchange(modelExchangeFunctions)
            }

            fmi2Type::fmi2CoSimulation => {
                let fmi2SetRealInputDerivatives = get_symbol::<fmi2SetRealInputDerivativesTYPE>(
                    &lib,
                    b"fmi2SetRealInputDerivatives",
                )?;
                let fmi2GetRealOutputDerivatives = get_symbol::<fmi2GetRealOutputDerivativesTYPE>(
                    &lib,
                    b"fmi2GetRealOutputDerivatives",
                )?;
                let fmi2DoStep = get_symbol::<fmi2DoStepTYPE>(&lib, b"fmi2DoStep")?;
                let fmi2CancelStep = get_symbol::<fmi2CancelStepTYPE>(&lib, b"fmi2CancelStep")?;
                let fmi2GetStatus = get_symbol::<fmi2GetStatusTYPE>(&lib, b"fmi2GetStatus")?;
                let fmi2GetRealStatus =
                    get_symbol::<fmi2GetRealStatusTYPE>(&lib, b"fmi2GetRealStatus")?;
                let fmi2GetIntegerStatus =
                    get_symbol::<fmi2GetIntegerStatusTYPE>(&lib, b"fmi2GetIntegerStatus")?;
                let fmi2GetBooleanStatus =
                    get_symbol::<fmi2GetBooleanStatusTYPE>(&lib, b"fmi2GetBooleanStatus")?;
                let fmi2GetStringStatus =
                    get_symbol::<fmi2GetStringStatusTYPE>(&lib, b"fmi2GetStringStatus")?;

                let coSimulationFunctions = CoSimulationFunctions {
                    fmi2SetRealInputDerivatives,
                    fmi2GetRealOutputDerivatives,
                    fmi2DoStep,
                    fmi2CancelStep,
                    fmi2GetStatus,
                    fmi2GetRealStatus,
                    fmi2GetIntegerStatus,
                    fmi2GetBooleanStatus,
                    fmi2GetStringStatus,
                };

                InterfaceType::CoSimulation(coSimulationFunctions)
            }
        };

        let mut fmu = FMU2 {
            instanceName: instanceName.to_string(),
            component: ptr::null_mut(),
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
            interfaceType,
        };

        fmu.component =
            fmu.instantiate(instanceName, guid, resourceUrl.as_ref(), visible, loggingOn);

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
            ptr::null() as fmi2String
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

        let interfaceType = match self.interfaceType {
            InterfaceType::ModelExchange(_) => fmi2Type::fmi2ModelExchange,
            InterfaceType::CoSimulation(_) => fmi2Type::fmi2CoSimulation,
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

    pub fn freeInstance(&mut self) {
        unsafe { (self.fmi2FreeInstance)(self.component) };
        if let Some(cb) = &self.logFMICall {
            cb(&fmi2OK, "fmi2FreeInstance()");
        }
    }

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

        let mut buffer: Vec<fmi2String> = vec![ptr::null(); values.len()];

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

    pub fn setString(&self, valueReferences: &[fmi2ValueReference], values: &[&str]) -> fmi2Status {
        debug_assert_eq!(valueReferences.len(), values.len());

        let values: Vec<CString> = values.iter().map(|&v| CString::new(v).unwrap()).collect();

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

    // FMI 2.0 Model Exchange specific types
    pub fn enterEventMode(&self) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2EnterEventMode)(self.component) };
            if let Some(cb) = &self.logFMICall {
                cb(&status, "fmi2EnterEventMode()");
            }
            status
        } else {
            panic!("fmi2EnterEventMode is only available for Model Exchange FMUs.");
        }
    }

    pub fn newDiscreteStates(&self, eventInfo: &mut fmi2EventInfo) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2NewDiscreteStates)(self.component, eventInfo) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2NewDiscreteStates(eventInfo={eventInfo:?})");
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2NewDiscreteStates is only available for Model Exchange FMUs.");
        }
    }

    pub fn enterContinuousTimeMode(&self) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2EnterContinuousTimeMode)(self.component) };
            if let Some(cb) = &self.logFMICall {
                cb(&status, "fmi2EnterContinuousTimeMode()");
            }
            status
        } else {
            panic!("fmi2EnterContinuousTimeMode is only available for Model Exchange FMUs.");
        }
    }

    pub fn completedIntegratorStep(
        &self,
        noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
        enterEventMode: &mut fmi2Boolean,
        terminateSimulation: &mut fmi2Boolean,
    ) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2CompletedIntegratorStep)(
                    self.component,
                    noSetFMUStatePriorToCurrentPoint,
                    enterEventMode,
                    terminateSimulation,
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2CompletedIntegratorStep(noSetFMUStatePriorToCurrentPoint={}, enterEventMode={}, terminateSimulation={})",
                    noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2CompletedIntegratorStep is only available for Model Exchange FMUs.");
        }
    }

    pub fn setTime(&self, time: fmi2Real) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2SetTime)(self.component, time) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2SetTime(time={})", time);
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2SetTime is only available for Model Exchange FMUs.");
        }
    }

    pub fn setContinuousStates(&self, x: &[fmi2Real]) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status =
                unsafe { (functions.fmi2SetContinuousStates)(self.component, x.as_ptr(), x.len()) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2SetContinuousStates(x={:?}, nx={})", x, x.len());
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2SetContinuousStates is only available for Model Exchange FMUs.");
        }
    }

    pub fn getDerivatives(&self, derivatives: &mut [fmi2Real]) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2GetDerivatives)(
                    self.component,
                    derivatives.as_mut_ptr(),
                    derivatives.len(),
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2GetDerivatives(derivatives={:?}, nx={})",
                    derivatives,
                    derivatives.len()
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetDerivatives is only available for Model Exchange FMUs.");
        }
    }

    pub fn getEventIndicators(&self, eventIndicators: &mut [fmi2Real]) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2GetEventIndicators)(
                    self.component,
                    eventIndicators.as_mut_ptr(),
                    eventIndicators.len(),
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2GetEventIndicators(eventIndicators={:?}, ni={})",
                    eventIndicators,
                    eventIndicators.len()
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetEventIndicators is only available for Model Exchange FMUs.");
        }
    }

    pub fn getContinuousStates(&self, x: &mut [fmi2Real]) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2GetContinuousStates)(self.component, x.as_mut_ptr(), x.len())
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2GetContinuousStates(x={:?}, nx={})", x, x.len());
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetContinuousStates is only available for Model Exchange FMUs.");
        }
    }

    pub fn getNominalsOfContinuousStates(&self, x_nominal: &mut [fmi2Real]) -> fmi2Status {
        if let InterfaceType::ModelExchange(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2GetNominalsOfContinuousStates)(
                    self.component,
                    x_nominal.as_mut_ptr(),
                    x_nominal.len(),
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2GetNominalsOfContinuousStates(x_nominal={:?}, nx={})",
                    x_nominal,
                    x_nominal.len()
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetNominalsOfContinuousStates is only available for Model Exchange FMUs.");
        }
    }

    // Co-Simulation specific methods
    pub fn setRealInputDerivatives(
        &self,
        vr: &[fmi2ValueReference],
        order: &[fmi2Integer],
        value: &[fmi2Real],
    ) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2SetRealInputDerivatives)(
                    self.component,
                    vr.as_ptr(),
                    vr.len(),
                    order.as_ptr(),
                    value.as_ptr(),
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2SetRealInputDerivatives(vr={:?}, nrv={}, order={:?}, value={:?})",
                    vr,
                    vr.len(),
                    order,
                    value
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2SetRealInputDerivatives is only available for Co-Simulation FMUs.");
        }
    }

    pub fn getRealOutputDerivatives(
        &self,
        vr: &[fmi2ValueReference],
        order: &[fmi2Integer],
        value: &mut [fmi2Real],
    ) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2GetRealOutputDerivatives)(
                    self.component,
                    vr.as_ptr(),
                    vr.len(),
                    order.as_ptr(),
                    value.as_mut_ptr(),
                )
            };
            if let Some(cb) = &self.logFMICall {
                let message = format!(
                    "fmi2GetRealOutputDerivatives(vr={:?}, nrv={}, order={:?}, value={:?})",
                    vr,
                    vr.len(),
                    order,
                    value
                );
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetRealOutputDerivatives is only available for Co-Simulation FMUs.");
        }
    }

    pub fn doStep(
        &self,
        currentCommunicationPoint: fmi2Real,
        communicationStepSize: fmi2Real,
        noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
    ) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe {
                (functions.fmi2DoStep)(
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
        } else {
            panic!("fmi2DoStep is only available for Co-Simulation FMUs.");
        }
    }

    pub fn cancelStep(&self) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2CancelStep)(self.component) };
            if let Some(cb) = &self.logFMICall {
                cb(&status, "fmi2CancelStep()");
            }
            status
        } else {
            fmi2Error
        }
    }

    pub fn getRealStatus(&self, s: &fmi2StatusKind, value: &mut fmi2Real) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2GetRealStatus)(self.component, *s, value) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2GetRealStatus(s={s:?}, value={value})");
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetRealStatus is only available for Co-Simulation FMUs.");
        }
    }

    pub fn getIntegerStatus(&self, s: &fmi2StatusKind, value: &mut fmi2Integer) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2GetIntegerStatus)(self.component, *s, value) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2GetIntegerStatus(s={s:?}, value={value})");
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetIntegerStatus is only available for Co-Simulation FMUs.");
        }
    }

    pub fn getBooleanStatus(&self, s: &fmi2StatusKind, value: &mut fmi2Boolean) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let status = unsafe { (functions.fmi2GetBooleanStatus)(self.component, *s, value) };
            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2GetBooleanStatus(s={s:?}, value={value})");
                cb(&status, message.as_str());
            }
            status
        } else {
            panic!("fmi2GetBooleanStatus is only available for Co-Simulation FMUs.");
        }
    }

    pub fn getStringStatus(&self, s: &fmi2StatusKind, value: &mut String) -> fmi2Status {
        if let InterfaceType::CoSimulation(functions) = &self.interfaceType {
            let mut buffer: fmi2String = ptr::null();

            let status =
                unsafe { (functions.fmi2GetStringStatus)(self.component, *s, &mut buffer) };

            if status == fmi2OK && !buffer.is_null() {
                *value = unsafe { CStr::from_ptr(buffer).to_string_lossy().into_owned() };
            }

            if let Some(cb) = &self.logFMICall {
                let message = format!("fmi2GetStringStatus(s={s:?}, value={value})");
                cb(&status, message.as_str());
            }

            status
        } else {
            panic!("fmi2GetStringStatus is only available for Co-Simulation FMUs.");
        }
    }
}

// Explicitly implement Sync for FMU2 since all fields are Sync
unsafe impl Sync for FMU2 {}
