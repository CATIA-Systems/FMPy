#![allow(non_camel_case_types, non_snake_case, unused_variables)]

use std::{
    cell::RefCell,
    ffi::{CString, c_void},
    path::Path,
    println,
    sync::Arc,
    todo, vec,
};

use approx::{relative_eq, relative_ne};
use fmi_rs::{
    fmi2::{
        CS, FMU2, types::{
            fmi2Boolean, fmi2False, fmi2Integer, fmi2Real, fmi2Status, fmi2StatusKind, fmi2True,
            fmi2ValueReference,
        },
    }, fmi3::{
        FMU3,
        types::{
            fmi3Boolean, fmi3Float32, fmi3Float64, fmi3InstanceEnvironment, fmi3Int8, fmi3Int16,
            fmi3Int32, fmi3Int64, fmi3LogMessageCallback,
            fmi3Status::{self},
            fmi3String, fmi3UInt8, fmi3UInt16, fmi3UInt32, fmi3UInt64, fmi3ValueReference,
        },
    },
};
use crate::conf::*;

pub mod conf;
pub mod fmi2;
pub mod fmi3;

#[derive(Debug, Clone, Copy, PartialEq, PartialOrd)]
enum fmiStatus {
    fmiOK,
    fmiWarning,
    fmiError,
}

type fmiFloat32 = f32;
type fmiFloat64 = f64;
type fmiInt8 = i8;
type fmiUInt8 = u8;
type fmiInt16 = i16;
type fmiUInt16 = u16;
type fmiInt32 = i32;
type fmiUInt32 = u32;
type fmiInt64 = i64;
type fmiUInt64 = u64;
type fmiBoolean = bool;
type fmiByte = u8;
type fmiClock = bool;
type fmiValueReference = u32;

impl From<fmi2Status> for fmiStatus {
    fn from(source: fmi2Status) -> Self {
        match source {
            fmi2Status::fmi2OK => fmiStatus::fmiOK,
            fmi2Status::fmi2Warning => fmiStatus::fmiWarning,
            _ => fmiStatus::fmiError,
        }
    }
}

impl From<fmiStatus> for fmi2Status {
    fn from(val: fmiStatus) -> Self {
        match val {
            fmiStatus::fmiOK => fmi2Status::fmi2OK,
            fmiStatus::fmiWarning => fmi2Status::fmi2Warning,
            fmiStatus::fmiError => fmi2Status::fmi2Error,
        }
    }
}

impl From<fmi3Status> for fmiStatus {
    fn from(source: fmi3Status) -> Self {
        match source {
            fmi3Status::fmi3OK => fmiStatus::fmiOK,
            fmi3Status::fmi3Warning => fmiStatus::fmiWarning,
            _ => fmiStatus::fmiError,
        }
    }
}

impl From<fmiStatus> for fmi3Status {
    fn from(val: fmiStatus) -> Self {
        match val {
            fmiStatus::fmiOK => fmi3Status::fmi3OK,
            fmiStatus::fmiWarning => fmi3Status::fmi3Warning,
            fmiStatus::fmiError => fmi3Status::fmi3Error,
        }
    }
}

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

const LOG_STATUS_ERROR: fmi3String = "logStatusError\0".as_ptr() as fmi3String;
const LOG_FMI_CALLS: fmi3String = "logFMICalls\0".as_ptr() as fmi3String;
const LOG_NESTED: fmi3String = "logNested\0".as_ptr() as fmi3String;

enum FMUInstance {
    FMI2(Box<FMU2<CS>>),
    FMI3(Arc<FMU3>),
}

struct Container {
    tolerance: Option<f64>,
    startTime: f64,
    stopTime: Option<f64>,
    nSteps: u64,
    terminated: bool,
    instances: Vec<FMUInstance>,
    system: System,
    stringValues: Vec<CString>,
    f32_buffer: Vec<f32>,
    f64_buffer: Vec<f64>,
    i8_buffer: Vec<i8>,
    u8_buffer: Vec<u8>,
    i16_buffer: Vec<i16>,
    u16_buffer: Vec<u16>,
    i32_buffer: Vec<i32>,
    u32_buffer: Vec<u32>,
    i64_buffer: Vec<i64>,
    u64_buffer: Vec<u64>,
    bool_buffer: Vec<bool>,
    string_buffer: Vec<String>,
    binary_buffer: RefCell<Vec<Vec<u8>>>,
}

macro_rules! return_on_error {
    ($status:ident, $expression:expr) => {{
        let s = $expression;

        if !matches!(s, fmiStatus::fmiOK | fmiStatus::fmiWarning) {
            return s.into();
        }

        if s > $status {
            $status = s;
        }
    }};
}

macro_rules! set_variables {
    ($self:ident, $valueReferences:ident, $values:ident, $fmi2_setter:ident, $fmi3_setter:ident) => {{
        let mut status = fmiStatus::fmiOK;
        let mut i = 0;

        for valueReference in $valueReferences {
            let variable = match $self.getVariable(*valueReference, VariableType::Float64) {
                Ok(var) => var,
                Err(e) => {
                    $self.logError(e.as_str());
                    return fmiStatus::fmiError;
                }
            };

            let size = variable.size.unwrap_or(1);

            for mapping in &variable.mappings {
                let instance = &$self.instances[mapping.component as usize];
                return_on_error!(
                    status,
                    match instance {
                        FMUInstance::FMI2(fmu) => {
                            $fmi2_setter(&fmu, &[mapping.valueReference], &$values[i..i + size])
                                .into()
                        }
                        FMUInstance::FMI3(fmu) => {
                            $fmi3_setter(fmu, &[mapping.valueReference], &$values[i..i + size])
                                .into()
                        }
                    }
                );
            }

            i += size;
        }

        if i != $values.len() {
            let message = format!(
                "Expected number of elements in values to be {} but was {}.",
                i,
                $values.len()
            );
            $self.logError(&message);
            status = fmiStatus::fmiError;
        }

        status.into()
    }};
}

type ContainerLogMessageCallback = dyn Fn(&fmiStatus, &str, &str) + Send + Sync;
type ContainerLogFMICallCallback = dyn Fn(&fmiStatus, &str, &str) + Send + Sync;

macro_rules! set_start_value {
    ($self:ident, $value_references:ident, $start:ident, $setter:ident, $variable_type:ty) => {{
        let result: Result<Vec<$variable_type>, _> = $start.iter().map(|s| s.parse()).collect();
        if let Ok(values) = result {
            $self.$setter($value_references, &values)
        } else {
            let message = format!("Failed to parse start value \"{:?}\".", $start);
            $self.logError(&message);
            fmiStatus::fmiError
        }
    }};
}

/// Macro to check FMI status and return early if error or fatal
/// Usage: fmi_check_status!(status);
#[macro_export]
macro_rules! fmi_check_status {
    ($status:expr) => {{
        let __fmi_status = $status;
        if __fmi_status > fmiStatus::fmiWarning {
            return __fmi_status;
        }
    }};
}

struct ContainerLogger {
    component_name: String,
    log_message: Arc<ContainerLogMessageCallback>,
    log_fmi_call: Arc<ContainerLogFMICallCallback>,
}

impl fmi_rs::fmi2::log::Logger for ContainerLogger {
    fn log_call(&self, status: fmi2Status, message: &str) {
        (self.log_fmi_call)(&status.into(), &self.component_name, message);
    }

    fn log_message(&self, status: fmi2Status, category: &str, message: &str) {
        (self.log_message)(&status.into(), category, message)
    }
}

impl fmi_rs::fmi3::log::Logger for ContainerLogger {
    fn log_call(&self, status: fmi3Status, message: &str) {
        (self.log_fmi_call)(&status.into(), &self.component_name, message);
    }

    fn log_message(&self, status: fmi3Status, category: &str, message: &str) {
        (self.log_message)(&status.into(), category, message)
    }
}

impl Container {
    fn instantiate(
        instantiation_token: &str,
        resource_path: &Path,
        log_message: Arc<ContainerLogMessageCallback>,
        log_fmi_call: Arc<ContainerLogFMICallCallback>,
        loggingOn: bool,
        visible: bool,
        instanceEnvironment: *mut c_void,
    ) -> Result<Self, String> {
        let config_path = resource_path.join("container.json");

        let system = match System::from_path(&config_path, instantiation_token) {
            Ok(system) => system,
            Err(error) => {
                let message = format!(
                    "Failed to read configuration file {}. {}",
                    config_path.to_string_lossy(),
                    error
                );
                return Err(message);
            }
        };

        let mut instances: Vec<FMUInstance> = Vec::new();

        for component in &system.components {
            let unzipdir = resource_path.join(&component.path);

            let logger = ContainerLogger {
                component_name: component.name.clone(),
                log_message: log_message.clone(), 
                log_fmi_call: log_fmi_call.clone() 
            };

            let fmu_instance: FMUInstance = match component.fmiMajorVersion {
                FMIMajorVersion::FMIMajorVersion2 => {
                    let component_name: String = component.name.clone();
                    match FMU2::<CS>::new(
                        &unzipdir,
                        &component.modelIdentifier,
                        &component.name,
                        &component.instantiationToken,
                        false,
                        loggingOn,
                        true,
                        Box::new(logger),
                        true,
                    ) {
                        Ok(fmu) => FMUInstance::FMI2(Box::new(fmu)),
                        Err(error) => {
                            let message = format!(
                                "Failed to instantiate the component {:?}. {:?}",
                                component.name, error
                            );
                            let message = CString::new(message).unwrap();
                            let message = message.as_ptr() as fmi3String;
                            todo!()
                        }
                    }
                }
                FMIMajorVersion::FMIMajorVersion3 => {
                    match FMU3::instantiateCoSimulation(
                        &unzipdir,
                        &component.modelIdentifier,
                        &component.name,
                        &component.instantiationToken,
                        false,
                        loggingOn,
                        false,
                        false,
                        Box::new(logger),
                        true,
                        None,
                    ) {
                        Ok(fmu) => FMUInstance::FMI3(fmu),
                        Err(error) => {
                            let message = format!(
                                "Failed to instantiate the component {:?}. {:?}",
                                component.name, error
                            );
                            let message = CString::new(message).unwrap();
                            let message = message.as_ptr() as fmi3String;
                            todo!()
                        }
                    }
                }
            };

            instances.push(fmu_instance);
        }

        let stringValues = Vec::new();

        let container = Container {
            tolerance: None,
            startTime: 0.0,
            stopTime: None,
            nSteps: 0,
            terminated: false,
            instances,
            system,
            stringValues,
            f32_buffer: Vec::new(),
            f64_buffer: Vec::new(),
            i8_buffer: Vec::new(),
            u8_buffer: Vec::new(),
            i16_buffer: Vec::new(),
            u16_buffer: Vec::new(),
            i32_buffer: Vec::new(),
            u32_buffer: Vec::new(),
            i64_buffer: Vec::new(),
            u64_buffer: Vec::new(),
            bool_buffer: Vec::new(),
            string_buffer: Vec::new(),
            binary_buffer: RefCell::new(Vec::new()),
        };

        let status = container.setStartValues();

        if !matches!(status, fmiStatus::fmiOK | fmiStatus::fmiWarning) {
            let message = "Failed to set start values.".to_string();
            return Err(message);
        }

        Ok(container)
    }

    fn setStartValues(&self) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;

        for (i, variable) in self.system.variables.iter().enumerate() {
            if let Some(start) = &variable.start {
                let valueReferences = &[(i + 1) as fmiValueReference];
                return_on_error!(
                    status,
                    match variable.variableType {
                        VariableType::Float32 =>
                            set_start_value!(self, valueReferences, start, setFloat32, fmiFloat32),
                        VariableType::Float64 =>
                            set_start_value!(self, valueReferences, start, setFloat64, fmiFloat64),
                        VariableType::Int8 =>
                            set_start_value!(self, valueReferences, start, setInt8, fmiInt8),
                        VariableType::UInt8 =>
                            set_start_value!(self, valueReferences, start, setUInt8, fmiUInt8),
                        VariableType::Int16 =>
                            set_start_value!(self, valueReferences, start, setInt16, fmiInt16),
                        VariableType::UInt16 =>
                            set_start_value!(self, valueReferences, start, setUInt16, fmiUInt16),
                        VariableType::Int32 =>
                            set_start_value!(self, valueReferences, start, setInt32, fmiInt32),
                        VariableType::UInt32 =>
                            set_start_value!(self, valueReferences, start, setUInt32, fmiUInt32),
                        VariableType::Int64 =>
                            set_start_value!(self, valueReferences, start, setInt64, fmiInt64),
                        VariableType::UInt64 =>
                            set_start_value!(self, valueReferences, start, setUInt64, fmiUInt64),
                        VariableType::Boolean =>
                            set_start_value!(self, valueReferences, start, setBoolean, fmiBoolean),
                        VariableType::String => {
                            let start: Vec<&str> = start.iter().map(String::as_str).collect();
                            self.setString(valueReferences, &start)
                        }
                        VariableType::Binary => {
                            let values: Result<Vec<Vec<fmiByte>>, Box<dyn std::error::Error>> =
                                start
                                    .iter()
                                    .map(|hex_str| {
                                        if hex_str.len() % 2 != 0 {
                                            return Err(format!(
                                                "Invalid hex string length: {}",
                                                hex_str
                                            )
                                            .into());
                                        }

                                        let mut bytes = Vec::new();

                                        for i in (0..hex_str.len()).step_by(2) {
                                            let byte_str = &hex_str[i..i + 2];
                                            match u8::from_str_radix(byte_str, 16) {
                                                Ok(byte) => bytes.push(byte),
                                                Err(e) => {
                                                    return Err(format!(
                                                        "Invalid hex byte '{}': {}",
                                                        byte_str, e
                                                    )
                                                    .into());
                                                }
                                            }
                                        }

                                        Ok(bytes)
                                    })
                                    .collect();

                            match values {
                                Ok(v) => self.setBinary(valueReferences, &v),
                                Err(e) => {
                                    self.logError("message");
                                    fmiStatus::fmiError
                                }
                            }
                        }
                        VariableType::Clock =>
                            set_start_value!(self, valueReferences, start, setClock, fmiClock),
                    }
                );
            }
        }

        status
    }

    fn logError(&self, message: &str) {
        println!("container::logError(message: {message})");
        // let message = CString::new(message).unwrap();
        // let message_ptr = message.as_ptr();
        // unsafe {
        //     (self.logMessage)(
        //         self.instanceEnvironment,
        //         fmiError,
        //         LOG_STATUS_ERROR,
        //         message_ptr,
        //     )
        // }
    }

    fn call_all<F, G>(&self, fmi2_function: F, fmi3_function: G) -> fmiStatus
    where
        F: Fn(&FMU2<CS>) -> fmi2Status,
        G: Fn(&FMU3) -> fmi3Status,
    {
        let mut status = fmiStatus::fmiOK;

        for instance in &self.instances {
            let s: fmiStatus = match instance {
                FMUInstance::FMI2(fmu) => fmi2_function(fmu).into(),
                FMUInstance::FMI3(fmu) => fmi3_function(fmu).into(),
            };
            if s >= fmiStatus::fmiError {
                return s;
            } else if s > status {
                status = s;
            }
        }
        status
    }

    pub fn enterInitializationMode(&self) -> fmiStatus {
        let fmi2_function = |fmu: &FMU2<CS>| {
            let status = fmu.setupExperiment(self.tolerance, self.startTime, self.stopTime);
            fmu.enterInitializationMode()
        };
        self.call_all(fmi2_function, |fmu| {
            fmu.enterInitializationMode(self.tolerance, self.startTime, self.stopTime)
        })
    }

    fn exitInitializationMode(&mut self) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;
        return_on_error!(status, self.updateConnections());
        return_on_error!(
            status,
            self.call_all(
                |fmu| fmu.exitInitializationMode(),
                |fmu| fmu.exitInitializationMode(),
            )
        );
        status
    }

    fn reset(&mut self) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;
        return_on_error!(status, self.call_all(|fmu| fmu.reset(), |fmu| fmu.reset()));
        return_on_error!(status, self.setStartValues());
        self.nSteps = 0;
        status
    }

    fn terminate(&self) -> fmiStatus {
        self.call_all(|fmu| fmu.terminate(), |fmu| fmu.terminate())
    }

    fn time(&self) -> f64 {
        self.startTime + self.nSteps as f64 * self.system.fixedStepSize
    }

    fn getVariable(
        &self,
        valueReference: fmi3ValueReference,
        variableType: VariableType,
    ) -> Result<&Variable, String> {
        let valueReference = valueReference as usize;
        if valueReference == 0 || valueReference > self.system.variables.len() {
            let message = format!(
                "Value reference {} is not valid for variable type {:?}.",
                valueReference, variableType
            );
            Err(message)
        } else {
            Ok(&self.system.variables[valueReference - 1])
        }
    }

    fn getFloat32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiFloat32],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiFloat32]| {
                self.logError("Not implemented.");
                fmiStatus::fmiError
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &mut [fmi3Float32]| {
                fmu.getFloat32(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getFloat64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiFloat64],
    ) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;
        let mut values = values;

        for valueReference in valueReferences {
            if *valueReference == 0 {
                values[0] = self.time();
                values = &mut values[1..];
            } else {
                let variable = match self.getVariable(*valueReference, VariableType::Float64) {
                    Ok(var) => var,
                    Err(e) => {
                        self.logError(e.as_str());
                        return fmiStatus::fmiError;
                    }
                };

                let mapping = &variable.mappings[0];

                let size = variable.size.unwrap_or(1);
                let instance = &self.instances[mapping.component as usize];

                let slice = match values.get_mut(0..size) {
                    Some(s) => s,
                    None => {
                        self.logError(
                            "Argument value is too small to hold the values of all variables.",
                        );
                        return fmiStatus::fmiError;
                    }
                };

                // TODO: check if valueReference is in range
                let valueReferences = &[mapping.valueReference];

                let s = match instance {
                    FMUInstance::FMI2(fmu) => fmu.getReal(valueReferences, slice).into(),
                    FMUInstance::FMI3(fmu) => fmu.getFloat64(valueReferences, slice).into(),
                };

                if s >= fmiStatus::fmiError {
                    return s;
                } else if s > status {
                    status = s;
                }

                values = &mut values[size..];
            }
        }

        let excess = values.len();

        if excess != 0 {
            self.logError("Argument value is too small to hold the values of all variables.");
            return fmiStatus::fmiError;
        }

        status
    }

    fn getInt8(&self, valueReferences: &[fmiValueReference], values: &mut [fmiInt8]) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiInt8]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Int8]| {
                fmu.getInt8(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt8(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt8],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiUInt8]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3UInt8]| {
                fmu.getUInt8(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt16(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt16],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiInt16]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiInt16]| {
                fmu.getInt16(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt16(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt16],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiUInt16]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt16]| {
                fmu.getUInt16(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt32],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmi2Integer]| {
                fmu.getInteger(valueReferences, values).into()
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Int32]| {
                fmu.getInt32(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt32],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiUInt32]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt32]| {
                fmu.getUInt32(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt64],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiInt64]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiInt64]| {
                fmu.getInt64(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt64],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiUInt64]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt64]| {
                fmu.getUInt64(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getBoolean(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiBoolean],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [fmiBoolean]| {
                let mut buffer = vec![0i32; values.len()];
                let status = fmu.getBoolean(valueReferences, &mut buffer);
                for (i, &value) in buffer.iter().enumerate() {
                    values[i] = value != fmi2False;
                }
                status.into()
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Boolean]| {
                fmu.getBoolean(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getString(
        &mut self,
        valueReferences: &[fmiValueReference],
        values: &mut [String],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [String]| {
                fmu.getString(valueReferences, values).into()
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [String]| {
                fmu.getString(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getBinary(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [Vec<fmiByte>],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2<CS>, valueReferences: &[fmiValueReference], values: &mut [Vec<fmiByte>]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [Vec<fmiByte>]| {
                fmu.getBinary(valueReferences, values).into()
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getValues<
        T,
        U: Fn(&FMU2<CS>, &[fmiValueReference], &mut [T]) -> fmiStatus,
        V: Fn(&FMU3, &[fmiValueReference], &mut [T]) -> fmiStatus,
    >(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [T],
        fmi2_getter: U,
        fmi3_getter: V,
    ) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;
        let mut values = values;

        for valueReference in valueReferences {
            let variable = match self.getVariable(*valueReference, VariableType::Float64) {
                Ok(var) => var,
                Err(e) => {
                    self.logError(e.as_str());
                    return fmiStatus::fmiError;
                }
            };

            let mapping = &variable.mappings[0];

            let size = variable.size.unwrap_or(1);
            let instance = &self.instances[mapping.component as usize];

            let slice = match values.get_mut(0..size) {
                Some(s) => s,
                None => {
                    self.logError(
                        "Argument value is too small to hold the values of all variables.",
                    );
                    return fmiStatus::fmiError;
                }
            };

            let vrs: [u32; 1] = [mapping.valueReference];

            let s = match instance {
                FMUInstance::FMI2(fmu) => fmi2_getter(fmu, &vrs, slice),
                FMUInstance::FMI3(fmu) => fmi3_getter(fmu, &vrs, slice),
            };

            if s >= fmiStatus::fmiError {
                return s;
            } else if s > status {
                status = s;
            }
            values = &mut values[size..];
        }

        let excess = values.len();

        if excess != 0 {
            self.logError("Argument value is too small to hold the values of all variables.");
            return fmiStatus::fmiError;
        }

        status
    }

    fn setFloat32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &[fmiFloat32],
    ) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiFloat32]| {
                let buffer: Vec<fmi2Real> = values.iter().map(|&v| v as fmi2Real).collect();
                fmu.setReal(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Float32]| {
                fmu.setFloat32(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setFloat64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &[fmiFloat64],
    ) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmi2Real]| {
                fmu.setReal(valueReferences, values)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Float64]| {
                fmu.setFloat64(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setInt8(&self, valueReferences: &[fmiValueReference], values: &[fmiInt8]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiInt8]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Int8]| {
                fmu.setInt8(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setUInt8(&self, valueReferences: &[fmiValueReference], values: &[fmiUInt8]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiUInt8]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3UInt8]| {
                fmu.setUInt8(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setInt16(&self, valueReferences: &[fmiValueReference], values: &[fmiInt16]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiInt16]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Int16]| {
                fmu.setInt16(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setUInt16(&self, valueReferences: &[fmiValueReference], values: &[fmiUInt16]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiUInt16]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3UInt16]| {
                fmu.setUInt16(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setInt32(&self, valueReferences: &[fmiValueReference], values: &[fmiInt32]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmi2Integer]| {
                fmu.setInteger(valueReferences, values)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Int32]| {
                fmu.setInt32(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setUInt32(&self, valueReferences: &[fmiValueReference], values: &[fmiUInt32]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiUInt32]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3UInt32]| {
                fmu.setUInt32(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setInt64(&self, valueReferences: &[fmiValueReference], values: &[fmiInt64]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiInt64]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Int64]| {
                fmu.setInt64(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setUInt64(&self, valueReferences: &[fmiValueReference], values: &[fmiUInt64]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiUInt64]| {
                let buffer: Vec<fmi2Integer> = values.iter().map(|&v| v as fmi2Integer).collect();
                fmu.setInteger(valueReferences, &buffer)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3UInt64]| {
                fmu.setUInt64(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setBoolean(
        &self,
        valueReferences: &[fmiValueReference],
        values: &[fmiBoolean],
    ) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[fmiBoolean]| {
                let values: Vec<fmi2Boolean> = values
                    .iter()
                    .map(|&v| if v { fmi2True } else { fmi2False })
                    .collect();
                fmu.setBoolean(valueReferences, &values)
            };
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmi3Boolean]| {
                fmu.setBoolean(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setString(&self, valueReferences: &[fmiValueReference], values: &[&str]) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2<CS>, valueReferences: &[fmi2ValueReference], values: &[&str]| {
                fmu.setString(valueReferences, values)
            };
        let fmi3_setter = |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[&str]| {
            fmu.setString(valueReferences, values)
        };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setBinary(&self, valueReferences: &[fmiValueReference], values: &[Vec<u8>]) -> fmiStatus {
        let fmi2_setter = |fmu: &FMU2<CS>,
                           valueReferences: &[fmi2ValueReference],
                           values: &[Vec<u8>]| fmiStatus::fmiError;
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[Vec<u8>]| {
                let values: Vec<&[u8]> = values.iter().map(|v| v.as_slice()).collect();
                fmu.setBinary(valueReferences, &values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setClock(&self, valueReferences: &[fmiValueReference], values: &[fmiBoolean]) -> fmiStatus {
        let fmi2_setter = |fmu: &FMU2<CS>,
                           valueReferences: &[fmi2ValueReference],
                           values: &[fmiBoolean]| fmiStatus::fmiError;
        let fmi3_setter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[fmiBoolean]| {
                fmu.setClock(valueReferences, values)
            };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn updateConnections(&mut self) -> fmiStatus {
        let status = fmiStatus::fmiOK;

        for connection in &self.system.connections {
            let srcInstance = &self.instances[connection.srcComponent];
            let dstInstance = &self.instances[connection.dstComponent];

            let size = connection.size.unwrap_or(1);

            let srcValueReferences = &connection.srcValueReferences;
            let dstValueReferences = &connection.dstValueReferences;

            match connection.variableType {
                VariableType::Float32 => {
                    self.f32_buffer.resize(size, 0.0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getFloat32(srcValueReferences, &mut self.f32_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setFloat32(dstValueReferences, &self.f32_buffer).into(),
                    });
                }
                VariableType::Float64 => {
                    self.f64_buffer.resize(size, 0.0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu
                            .getReal(srcValueReferences, &mut self.f64_buffer)
                            .into(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getFloat64(srcValueReferences, &mut self.f64_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) =>
                            fmu.setReal(dstValueReferences, &self.f64_buffer).into(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setFloat64(dstValueReferences, &self.f64_buffer).into(),
                    });
                }
                VariableType::Int8 => {
                    self.i8_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.getInt8(srcValueReferences, &mut self.i8_buffer).into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setInt8(dstValueReferences, &self.i8_buffer).into(),
                    });
                }
                VariableType::UInt8 => {
                    self.u8_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getUInt8(srcValueReferences, &mut self.u8_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setUInt8(dstValueReferences, &self.u8_buffer).into(),
                    });
                }
                VariableType::Int16 => {
                    self.i16_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getInt16(srcValueReferences, &mut self.i16_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setInt16(dstValueReferences, &self.i16_buffer).into(),
                    });
                }
                VariableType::UInt16 => {
                    self.u16_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getUInt16(srcValueReferences, &mut self.u16_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setUInt16(dstValueReferences, &self.u16_buffer).into(),
                    });
                }
                VariableType::Int32 => {
                    self.i32_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu
                            .getInteger(srcValueReferences, &mut self.i32_buffer)
                            .into(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getInt32(srcValueReferences, &mut self.i32_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) =>
                            fmu.setInteger(dstValueReferences, &self.i32_buffer).into(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setInt32(dstValueReferences, &self.i32_buffer).into(),
                    });
                }
                VariableType::UInt32 => {
                    self.u32_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getUInt32(srcValueReferences, &mut self.u32_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setUInt32(dstValueReferences, &self.u32_buffer).into(),
                    });
                }
                VariableType::Int64 => {
                    self.i64_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getInt64(srcValueReferences, &mut self.i64_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setInt64(dstValueReferences, &self.i64_buffer).into(),
                    });
                }
                VariableType::UInt64 => {
                    self.u64_buffer.resize(size, 0);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getUInt64(srcValueReferences, &mut self.u64_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setUInt64(dstValueReferences, &self.u64_buffer).into(),
                    });
                }
                VariableType::Boolean => {
                    self.bool_buffer.resize(size, false);
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => {
                            self.i32_buffer.resize(size, 0);
                            let status = fmu.getBoolean(srcValueReferences, &mut self.i32_buffer);
                            for (i, value) in self.i32_buffer.iter().enumerate() {
                                self.bool_buffer[i] = *value != fmi2False;
                            }
                            status.into()
                        }
                        FMUInstance::FMI3(fmu) => fmu
                            .getBoolean(srcValueReferences, &mut self.bool_buffer)
                            .into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => {
                            self.i32_buffer.resize(size, 0);
                            for (i, &value) in self.bool_buffer.iter().enumerate() {
                                self.i32_buffer[i] = if value { fmi2True } else { fmi2False };
                            }
                            fmu.setBoolean(dstValueReferences, &self.i32_buffer).into()
                        }
                        FMUInstance::FMI3(fmu) => fmu
                            .setBoolean(dstValueReferences, &self.bool_buffer)
                            .into(),
                    });
                }
                VariableType::String => {
                    self.string_buffer.resize(size, String::new());
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu
                            .getString(srcValueReferences, &mut self.string_buffer)
                            .into(),
                        FMUInstance::FMI3(fmu) => fmu
                            .getString(srcValueReferences, &mut self.string_buffer)
                            .into(),
                    });
                    let values: Vec<&str> = self.string_buffer.iter().map(String::as_str).collect();
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) =>
                            fmu.setString(dstValueReferences, &values).into(),
                        FMUInstance::FMI3(fmu) =>
                            fmu.setString(dstValueReferences, &values).into(),
                    });
                }
                VariableType::Binary => {
                    let mut buffer = self.binary_buffer.borrow_mut();
                    buffer.resize(size, Vec::new());
                    let buffer_ref = &mut buffer[..];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => {
                            self.logError("Binary variables are not supported for FMI 2.");
                            return fmiStatus::fmiError;
                        }
                        FMUInstance::FMI3(fmu) =>
                            fmu.getBinary(srcValueReferences, buffer_ref).into(),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => {
                            self.logError("Binary variables are not supported for FMI 2.");
                            return fmiStatus::fmiError;
                        }
                        FMUInstance::FMI3(fmu) => {
                            let slices: Vec<&[u8]> = buffer.iter().map(|v| v.as_slice()).collect();
                            fmu.setBinary(dstValueReferences, &slices[..]).into()
                        }
                    });
                }
                _ => {
                    self.logError(&format!(
                        "Connections of type {:?} are not supported.",
                        connection.variableType
                    ));
                    return fmiStatus::fmiError;
                }
            }
        }

        status
    }

    fn doFixedStep(&mut self) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;
        let communicationStepSize = self.system.fixedStepSize;
        let noSetFMUStatePriorToCurrentPoint = true;

        // Note: Direct parallelization of FMU instances is not possible due to
        // thread safety constraints (FMU callbacks are not Sync).
        // The FMU doStep calls must be executed sequentially.

        let currentCommunicationPoint = self.time();
        let communicationStepSize = self.system.fixedStepSize;

        let do_step = |instance: &FMUInstance| match instance {
            FMUInstance::FMI2(fmu) => {
                let status = fmu.doStep(currentCommunicationPoint, communicationStepSize, fmi2True);

                let mut terminated = fmi2False;

                if status == fmi2Status::fmi2Discard {
                    fmu.getBooleanStatus(&fmi2StatusKind::fmi2Terminated, &mut terminated);
                }

                (status.into(), terminated != fmi2False)
            }
            FMUInstance::FMI3(fmu) => {
                let mut eventHandlingNeeded = false;
                let mut terminateSimulation = false;
                let mut earlyReturn = false;
                let mut lastSuccessfulTime = 0.0;
                let status = fmu.doStep(
                    currentCommunicationPoint,
                    communicationStepSize,
                    true,
                    &mut eventHandlingNeeded,
                    &mut terminateSimulation,
                    &mut earlyReturn,
                    &mut lastSuccessfulTime,
                );
                (status.into(), terminateSimulation)
            }
        };

        let result: Vec<(fmiStatus, bool)> = if self.system.parallelDoStep {
            // self.instances.par_iter().map(do_step).collect()
            todo!()
        } else {
            self.instances.iter().map(do_step).collect()
        };

        for (do_step_status, terminated) in result {
            self.terminated |= terminated;
            if do_step_status > status {
                status = do_step_status;
            }
        }

        if !matches!(status, fmiStatus::fmiOK | fmiStatus::fmiWarning) || self.terminated {
            return status;
        }

        return_on_error!(status, self.updateConnections());

        self.nSteps += 1;

        status
    }

    fn doStep(
        &mut self,
        currentCommunicationPoint: fmiFloat64,
        communicationStepSize: fmiFloat64,
    ) -> fmiStatus {
        let mut status = fmiStatus::fmiOK;

        if relative_ne!(currentCommunicationPoint, self.time()) {
            let message = format!(
                "Expected currentCommunicationPoint={} but was {}",
                self.time(),
                currentCommunicationPoint
            );
            self.logError(&message);
            return fmiStatus::fmiError;
        }

        if communicationStepSize < 0.0 || relative_eq!(communicationStepSize, 0.0) {
            self.logError("Argument communicationStepSize must be greater than 0.");
            return fmiStatus::fmiError;
        }

        let n_steps_float = communicationStepSize / self.system.fixedStepSize;
        let n_steps = n_steps_float.round() as u64;

        if n_steps == 0 || !relative_eq!(n_steps as f64, n_steps_float) {
            let message = format!(
                "Argument communicationStepSize={} must be an even multiple of fixedStepSize={}.",
                communicationStepSize, self.system.fixedStepSize
            );
            self.logError(&message);
            return fmiStatus::fmiError;
        }

        for _ in 0..n_steps {
            return_on_error!(status, self.doFixedStep());
        }

        status
    }
}
