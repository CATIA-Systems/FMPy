#![allow(non_camel_case_types, non_snake_case, unused_variables)]

pub mod conf;
pub mod fmi2;
pub mod fmi3;

use crate::conf::*;
use approx::relative_ne;
use fmi::fmi2::types::*;
use fmi::fmi2::*;
use fmi::fmi3::types::*;
use fmi::fmi3::*;
use fmi::types::fmiStatus::*;
use fmi::types::*;
use fmi::*;
use rayon::prelude::*;
use serde_json::value;
use std::error::Error;
use std::ffi::CString;
use std::os::raw::c_void;
use std::path::Path;

use std::sync::Arc;

pub const VERSION: &str = env!("CARGO_PKG_VERSION");

const LOG_STATUS_ERROR: fmi3String = "logStatusError\0".as_ptr() as fmi3String;
const LOG_FMI_CALLS: fmi3String = "logFMICalls\0".as_ptr() as fmi3String;
const LOG_NESTED: fmi3String = "logNested\0".as_ptr() as fmi3String;

enum FMUInstance<'a> {
    FMI2(Box<FMU2<'a>>),
    FMI3(Box<FMU3<'a>>),
}

struct Container<'a> {
    time: f64,
    tolerance: Option<f64>,
    startTime: f64,
    stopTime: Option<f64>,
    terminated: bool,
    instances: Vec<FMUInstance<'a>>,
    system: System,
    logMessage: fmi3LogMessageCallback,
    instanceEnvironment: fmi3InstanceEnvironment,
    stringValues: Vec<CString>,
}

macro_rules! return_on_error {
    ($status:ident, $expression:expr) => {{
        let s = $expression;

        if !matches!(s, fmiOK | fmiWarning) {
            return s;
        }

        if s > $status {
            $status = s;
        }
    }};
}

macro_rules! set_variables {
    ($self:ident, $valueReferences:ident, $values:ident, $fmi2_setter:ident, $fmi3_setter:ident) => {{
        let mut status = fmiOK;
        let mut i = 0;

        for valueReference in $valueReferences {
            let variable = match $self.getVariable(*valueReference, VariableType::Float64) {
                Ok(var) => var,
                Err(e) => {
                    $self.logError(e.as_str());
                    return fmi3Error;
                }
            };

            let size = variable.size.unwrap_or(1);

            for mapping in &variable.mappings {
                let instance = &$self.instances[mapping.component as usize];
                return_on_error!(
                    status,
                    match instance {
                        FMUInstance::FMI2(fmu) => {
                            $fmi2_setter(fmu, &[mapping.valueReference], &$values[i..i + size])
                        }
                        FMUInstance::FMI3(fmu) => {
                            $fmi3_setter(fmu, &[mapping.valueReference], &$values[i..i + size])
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
            status = fmiError;
        }

        status
    }};
}

type ContainerLogMessageCallback = dyn Fn(&fmiStatus, &str, &str) + Send + Sync;
type ContainerLogFMICallCallback = dyn Fn(&fmiStatus, &str, &str) + Send + Sync;

// impl<'a> Drop for Container<'a> {
//     fn drop(&mut self) {
//         for instance in &mut self.instances {
//             match instance {
//                 FMUInstance::FMI2(fmu) => fmu.freeInstance(),
//                 FMUInstance::FMI3(fmu) => fmu.freeInstance(),
//             }
//         }
//     }
// }

macro_rules! set_start_value {
    ($self:ident, $value_references:ident, $start:ident, $setter:ident, $variable_type:ty) => {{
        let result: Result<Vec<$variable_type>, _> = $start.iter().map(|s| s.parse()).collect();
        if let Ok(values) = result {
            $self.$setter($value_references, &values)
        } else {
            let message = format!("Failed to parse start value \"{:?}\".", $start);
            $self.logError(&message);
            fmiError
        }
    }};
}

impl Container<'_> {
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

            // let shared_library_name =
            //     format!("{}{}", component.modelIdentifier, SHARED_LIBRARY_EXTENSION);

            // let platform_dir = match component.fmiMajorVersion {
            //     FMIMajorVersion::FMIMajorVersion2 => fmi::fmi2::PLATFORM,
            //     FMIMajorVersion::FMIMajorVersion3 => fmi::fmi3::PLATFORM_TUPLE,
            // };

            // let shared_library_path = resource_path
            //     .join(&component.path)
            //     .join("binaries")
            //     .join(platform_dir)
            //     .join(shared_library_name);

            let name = component.name.clone();
            let log_fmi_call_clone = log_fmi_call.clone();

            let log_component_fmi_call = move |status: &fmi3Status, message: &str| {
                (log_fmi_call_clone)(&status, &name, message);
            };

            let component_name = component.name.clone();
            // Create a thread-safe wrapper for the instance environment pointer
            // SAFETY: We assume the instanceEnvironment pointer remains valid for the lifetime of the FMU
            let userdata_ptr = instanceEnvironment as usize;

            let log_component_message =
                move |status: &fmi3Status, category: &str, message: &str| {
                    let message = format!("[{component_name}] {message}");
                    let message = CString::new(message).unwrap();
                    logMessage(
                        userdata_ptr as *mut c_void,
                        *status,
                        LOG_NESTED,
                        message.as_ptr() as fmi3String,
                    );
                };

            let fmu_instance = match component.fmiMajorVersion {
                FMIMajorVersion::FMIMajorVersion2 => {
                    let component_name: String = component.name.clone();
                    match FMU2::new(
                        &unzipdir,
                        &component.modelIdentifier,
                        &component.name,
                        fmi2Type::fmi2CoSimulation,
                        &component.instantiationToken,
                        false,
                        loggingOn,
                        if loggingOn {
                            Some(Box::new(log_component_fmi_call))
                        } else {
                            None
                        },
                        Some(Box::new(log_component_message)),
                    ) {
                        Ok(fmu) => FMUInstance::FMI2(Box::new(fmu)),
                        Err(error) => {
                            let message = format!("Failed to instantiate the component {:?}. {:?}",
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
                        &[],
                        if loggingOn {
                            Some(Box::new(log_component_fmi_call))
                        } else {
                            None
                        },
                        Some(Box::new(log_component_message)),
                    ) {
                        Ok(fmu) => FMUInstance::FMI3(Box::new(fmu)),
                        Err(error) => {
                            let message = format!("Failed to instantiate the component {:?}. {:?}",
                                component.name, error
                            );
                            let message = CString::new(message).unwrap();
                            let message = message.as_ptr() as fmi3String;
                            todo!()
                        }
                    }
                }
            };

            // let component_resource_path = resource_path
            //     .join(&component.path)
            //     .join("resources")
            //     .join("");

            // let status = match &mut fmu_instance {
            //     FMUInstance::FMI2(fmu) => {
            //         let resource_url = if component_resource_path.is_dir() {
            //             Some(Url::from_directory_path(&component_resource_path).unwrap())
            //         } else {
            //             None
            //         };
            //         fmu.instantiate(
            //             &component.name,
            //             fmi2Type::fmi2CoSimulation,
            //             &component.instantiationToken,
            //             resource_url.as_ref(),
            //             visible,
            //             loggingOn,
            //         )
            //     }
            //     FMUInstance::FMI3(fmu) => {
            //         let resource_path = if component_resource_path.is_dir() {
            //             Some(component_resource_path.as_path())
            //         } else {
            //             None
            //         };
            //         fmu.instantiateCoSimulation(
            //             &component.name,
            //             &component.instantiationToken,
            //             resource_path,
            //             visible,
            //             loggingOn,
            //             false,
            //             false,
            //             &[],
            //         )
            //     }
            // };

            // if !matches!(status, fmiOK | fmiWarning) {
            //     let message = format!("Failed to instantiate component {}.", component.name);
            //     return Err(message);
            // }

            instances.push(fmu_instance);
        }

        let stringValues = Vec::new();

        let container = Container {
            time: 0.0,
            tolerance: None,
            startTime: 0.0,
            stopTime: None,
            terminated: false,
            instances,
            system,
            logMessage,
            instanceEnvironment,
            stringValues,
        };

        let status = container.setStartValues();

        if !matches!(status, fmiOK | fmiWarning) {
            let message = format!("Failed to set start values.");
            return Err(message);
        }

        Ok(container)
    }

    fn setStartValues(&self) -> fmiStatus {

        let mut status = fmiOK;

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
                        VariableType::Boolean | VariableType::Clock =>
                            set_start_value!(self, valueReferences, start, setBoolean, fmiBoolean),
                        VariableType::String => {
                            let start: Vec<&str> = start.iter().map(String::as_str).collect();
                            self.setString(valueReferences, &start)
                        },
                        VariableType::Binary => {
                            let values: Result<Vec<Vec<fmiByte>>, Box<dyn Error>> = start.into_iter().map(|hex_str| {
                                    
                                    if hex_str.len() % 2 != 0 {
                                        return Err(format!("Invalid hex string length: {}", hex_str).into());
                                    }
                                    
                                    let mut bytes = Vec::new();

                                    for i in (0..hex_str.len()).step_by(2) {
                                        let byte_str = &hex_str[i..i+2];
                                        match u8::from_str_radix(byte_str, 16) {
                                            Ok(byte) => bytes.push(byte),
                                            Err(e) => return Err(format!("Invalid hex byte '{}': {}", byte_str, e).into()),
                                        }
                                    }

                                    Ok(bytes)
                                })
                                .collect();

                            match values {
                                Ok(v) => {
                                    self.setBinary(valueReferences, &v)
                                },
                                Err(e) => {
                                    self.logError("message");
                                    fmiError
                                }
                            }
                            
                        },
                        // _ => {
                        //     let message = format!(
                        //         "Start value of type {:?} is not supported.",
                        //         variable.variableType
                        //     );
                        //     self.logError(&message);
                        //     fmiError
                        // }
                    }
                );
            }
        }

        status
    }

    fn logError(&self, message: &str) {
        let message = CString::new(message).unwrap();
        let message_ptr = message.as_ptr();
        unsafe {
            (self.logMessage)(
                self.instanceEnvironment,
                fmiError,
                LOG_STATUS_ERROR,
                message_ptr,
            )
        }
    }

    fn call_all<F, G>(&self, fmi2_function: F, fmi3_function: G) -> fmi3Status
    where
        F: Fn(&FMU2) -> fmi2Status,
        G: Fn(&FMU3) -> fmi3Status,
    {
        let mut status = fmiOK;

        for instance in &self.instances {
            let s = match instance {
                FMUInstance::FMI2(fmu) => {
                    let status = fmi2_function(fmu);
                    fmi3Status::try_from(status as i32).unwrap()
                }
                FMUInstance::FMI3(fmu) => fmi3_function(fmu),
            };
            if s > fmi3Error {
                return s;
            } else if s > status {
                status = s;
            }
        }
        status
    }

    pub fn enterInitializationMode(&self) -> fmiStatus {
        let fmi2_function = |fmu: &FMU2| {
            let status = fmu.setupExperiment(self.tolerance, self.startTime, self.stopTime);
            fmu.enterInitializationMode()
        };
        self.call_all(fmi2_function, |fmu| {
            fmu.enterInitializationMode(self.tolerance, self.startTime, self.stopTime)
        })
    }

    fn exitInitializationMode(&self) -> fmiStatus {
        let mut status = fmiOK;
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

    fn reset(&self) -> fmiStatus {
        let mut status = fmiOK;
        return_on_error!(status, self.call_all(|fmu| fmu.reset(), |fmu| fmu.reset()));
        return_on_error!(status, self.setStartValues());
        status
    }

    fn terminate(&self) -> fmiStatus {
        self.call_all(|fmu| fmu.terminate(), |fmu| fmu.terminate())
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
            Err(String::from(message))
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
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiFloat32]| {
                self.logError("Not implemented.");
                fmiError
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &mut [fmi3Float32]| {
                fmu.getFloat32(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getFloat64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiFloat64],
    ) -> fmiStatus {
        let mut status = fmiOK;
        let mut values = values;

        for valueReference in valueReferences {
            if *valueReference == 0 {
                values[0] = self.time;
                values = &mut values[1..];
            } else {
                let variable = match self.getVariable(*valueReference, VariableType::Float64) {
                    Ok(var) => var,
                    Err(e) => {
                        self.logError(e.as_str());
                        return fmi3Error;
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
                        return fmi3Error;
                    }
                };

                // TODO: check if valueReference is in range
                let valueReferences = &[mapping.valueReference];

                let s = match instance {
                    FMUInstance::FMI2(fmu) => fmu.getReal(valueReferences, slice),
                    FMUInstance::FMI3(fmu) => fmu.getFloat64(valueReferences, slice),
                };

                if s >= fmi3Error {
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
            return fmi3Error;
        }

        status
    }

    fn getInt8(&self, valueReferences: &[fmiValueReference], values: &mut [fmiInt8]) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiInt8]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Int8]| {
                fmu.getInt8(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt8(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt8],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiUInt8]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3UInt8]| {
                fmu.getUInt8(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt16(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt16],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiInt16]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiInt16]| {
                fmu.getInt16(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt16(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt16],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiUInt16]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt16]| {
                fmu.getUInt16(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt32],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmi2Integer]| {
                fmu.getInteger(valueReferences, values)
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Int32]| {
                fmu.getInt32(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt32],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiUInt32]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt32]| {
                fmu.getUInt32(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getInt64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiInt64],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiInt64]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiInt64]| {
                fmu.getInt64(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getUInt64(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiUInt64],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiUInt64]| {
                todo!();
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmiUInt64]| {
                fmu.getUInt64(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getBoolean(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [fmiBoolean],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [fmiBoolean]| {
                let mut buffer = vec![0i32; values.len()];
                let status = fmu.getBoolean(valueReferences, &mut buffer);
                for (i, &value) in buffer.iter().enumerate() {
                    values[i] = value != fmi2False;
                }
                status
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [fmi3Boolean]| {
                fmu.getBoolean(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getString(
        &mut self,
        valueReferences: &[fmiValueReference],
        values: &mut [String],
    ) -> fmiStatus {
        let fmi2_getter =
            |fmu: &FMU2, valueReferences: &[fmiValueReference], values: &mut [String]| {
                fmu.getString(valueReferences, values)
            };
        let fmi3_getter =
            |fmu: &FMU3, valueReferences: &[fmiValueReference], values: &mut [String]| {
                fmu.getString(valueReferences, values)
            };
        self.getValues(valueReferences, values, fmi2_getter, fmi3_getter)
    }

    fn getBinary(
        &self,
        valueReferences: &[fmiValueReference],
        sizes: &mut [usize],
        values: &mut [fmiBinary],
    ) -> fmiStatus {
        let mut status = fmiOK;
        let mut size_idx = 0;
        let mut value_idx = 0;

        for valueReference in valueReferences {
            let variable = match self.getVariable(*valueReference, VariableType::Binary) {
                Ok(var) => var,
                Err(e) => {
                    self.logError(e.as_str());
                    return fmi3Error;
                }
            };

            let mapping = &variable.mappings[0];
            let var_size = variable.size.unwrap_or(1);
            let instance = &self.instances[mapping.component as usize];

            if size_idx + var_size > sizes.len() || value_idx + var_size > values.len() {
                self.logError("Argument sizes or values array is too small.");
                return fmi3Error;
            }

            let size_slice = &mut sizes[size_idx..size_idx + var_size];
            let value_slice = &mut values[value_idx..value_idx + var_size];
            let vrs: [u32; 1] = [mapping.valueReference];

            let s = match instance {
                FMUInstance::FMI2(fmu) => {
                    self.logError("Binary variables are not supported for FMI 2.");
                    fmiError
                }
                FMUInstance::FMI3(fmu) => fmu.getBinary(&vrs, size_slice, value_slice),
            };

            if s >= fmiError {
                return s;
            } else if s > status {
                status = s;
            }

            size_idx += var_size;
            value_idx += var_size;
        }

        status
    }

    fn getValues<
        T,
        U: Fn(&FMU2, &[fmiValueReference], &mut [T]) -> fmiStatus,
        V: Fn(&FMU3, &[fmiValueReference], &mut [T]) -> fmiStatus,
    >(
        &self,
        valueReferences: &[fmiValueReference],
        values: &mut [T],
        fmi2_getter: U,
        fmi3_getter: V,
    ) -> fmiStatus {
        let mut status = fmiOK;
        let mut values = values;

        for valueReference in valueReferences {
            let variable = match self.getVariable(*valueReference, VariableType::Float64) {
                Ok(var) => var,
                Err(e) => {
                    self.logError(e.as_str());
                    return fmi3Error;
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
                    return fmi3Error;
                }
            };

            let vrs: [u32; 1] = [mapping.valueReference];

            let s = match instance {
                FMUInstance::FMI2(fmu) => fmi2_getter(fmu, &vrs, slice),
                FMUInstance::FMI3(fmu) => fmi3_getter(fmu, &vrs, slice),
            };

            if s >= fmiError {
                return s;
            } else if s > status {
                status = s;
            }
            values = &mut values[size..];
        }

        let excess = values.len();

        if excess != 0 {
            self.logError("Argument value is too small to hold the values of all variables.");
            return fmi3Error;
        }

        status
    }

    fn setFloat32(
        &self,
        valueReferences: &[fmiValueReference],
        values: &[fmiFloat32],
    ) -> fmiStatus {
        let fmi2_setter =
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiFloat32]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmi2Real]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiInt8]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiUInt8]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiInt16]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiUInt16]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmi2Integer]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiUInt32]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiInt64]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiUInt64]| {
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
            |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[fmiBoolean]| {
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
        let fmi2_setter = |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[&str]| {
            fmu.setString(valueReferences, values)
        };
        let fmi3_setter = |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[&str]| {
            fmu.setString(valueReferences, values)
        };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn setBinary(&self, valueReferences: &[fmiValueReference], values: &[Vec<u8>]) -> fmiStatus {
        let fmi2_setter = |fmu: &FMU2, valueReferences: &[fmi2ValueReference], values: &[Vec<u8>]| {
            fmiError
        };
        let fmi3_setter = |fmu: &FMU3, valueReferences: &[fmi3ValueReference], values: &[Vec<u8>]| {
            let sizes: Vec<usize> = values.iter().map(|v| v.len()).collect();
            let values: Vec<*const u8> = values.iter().map(|v| v.as_ptr()).collect();
            fmu.setBinary(valueReferences, &sizes, &values)
        };
        set_variables!(self, valueReferences, values, fmi2_setter, fmi3_setter)
    }

    fn updateConnections(&self) -> fmiStatus {
        let status = fmiOK;

        for connection in &self.system.connections {
            let srcInstance = &self.instances[connection.srcComponent];
            let dstInstance = &self.instances[connection.dstComponent];

            let size = connection.size.unwrap_or(1);

            let srcValueReferences = &connection.srcValueReferences;
            let dstValueReferences = &connection.dstValueReferences;

            match connection.variableType {
                VariableType::Float32 => {
                    let mut values = vec![0f32; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getFloat32(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setFloat32(&dstValueReferences, &values),
                    });
                }
                VariableType::Float64 => {
                    let mut values = vec![0f64; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu.getReal(&srcValueReferences, &mut values),
                        FMUInstance::FMI3(fmu) => fmu.getFloat64(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => fmu.setReal(&dstValueReferences, &values),
                        FMUInstance::FMI3(fmu) => fmu.setFloat64(&dstValueReferences, &values),
                    });
                }
                VariableType::Int8 => {
                    let mut values = vec![0i8; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getInt8(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setInt8(&dstValueReferences, &values),
                    });
                }
                VariableType::UInt8 => {
                    let mut values = vec![0u8; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getUInt8(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setUInt8(&dstValueReferences, &values),
                    });
                }
                VariableType::Int16 => {
                    let mut values = vec![0i16; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getInt16(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setInt16(&dstValueReferences, &values),
                    });
                }
                VariableType::UInt16 => {
                    let mut values = vec![0u16; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getUInt16(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setUInt16(&dstValueReferences, &values),
                    });
                }
                VariableType::Int32 => {
                    let mut values = vec![0i32; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu.getInteger(&srcValueReferences, &mut values),
                        FMUInstance::FMI3(fmu) => fmu.getInt32(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => fmu.setInteger(&dstValueReferences, &values),
                        FMUInstance::FMI3(fmu) => fmu.setInt32(&dstValueReferences, &values),
                    });
                }
                VariableType::UInt32 => {
                    let mut values = vec![0u32; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getUInt32(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setUInt32(&dstValueReferences, &values),
                    });
                }
                VariableType::Int64 => {
                    let mut values = vec![0i64; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getInt64(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setInt64(&dstValueReferences, &values),
                    });
                }
                VariableType::UInt64 => {
                    let mut values = vec![0u64; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.getUInt64(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => todo!(),
                        FMUInstance::FMI3(fmu) => fmu.setUInt64(&dstValueReferences, &values),
                    });
                }
                VariableType::Boolean => {
                    let mut values = vec![false; size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => {
                            let mut buffer = vec![fmi2False; size];
                            let status = fmu.getBoolean(&srcValueReferences, &mut buffer);
                            for (i, value) in buffer.iter().enumerate() {
                                values[i] = buffer[i] != fmi2False;
                            }
                            status
                        }
                        FMUInstance::FMI3(fmu) => fmu.getBoolean(&srcValueReferences, &mut values),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => {
                            let buffer: Vec<fmi2Boolean> = values
                                .iter()
                                .map(|&v| if v { fmi2True } else { fmi2False })
                                .collect();
                            fmu.setBoolean(&dstValueReferences, &buffer)
                        }
                        FMUInstance::FMI3(fmu) => fmu.setBoolean(&dstValueReferences, &values),
                    });
                }
                VariableType::String => {
                    let mut values = vec![String::new(); size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => fmu.getString(&srcValueReferences, &mut values),
                        FMUInstance::FMI3(fmu) => fmu.getString(&srcValueReferences, &mut values),
                    });
                    let values: Vec<&str> = values.iter().map(String::as_str).collect();
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) => fmu.setString(&dstValueReferences, &values),
                        FMUInstance::FMI3(fmu) => fmu.setString(&dstValueReferences, &values),
                    });
                }
                VariableType::Binary => {
                    let mut sizes = vec![0usize; size];
                    let mut value_ptrs = vec![std::ptr::null::<u8>(); size];
                    fmi_check_status!(match srcInstance {
                        FMUInstance::FMI2(fmu) => {
                            self.logError("Binary variables are not supported for FMI 2.");
                            return fmiError; 
                        },
                        FMUInstance::FMI3(fmu) => fmu.getBinary(&srcValueReferences, &mut sizes, &mut value_ptrs),
                    });
                    fmi_check_status!(match dstInstance {
                        FMUInstance::FMI2(fmu) =>  {
                            self.logError("Binary variables are not supported for FMI 2.");
                            return fmiError; 
                        },
                        FMUInstance::FMI3(fmu) => fmu.setBinary(&dstValueReferences, &sizes, &value_ptrs),
                    });
                }
                _ => {
                    self.logError(&format!(
                        "Connections of type {:?} are not supported.",
                        connection.variableType
                    ));
                    return fmiError;
                }
            }
        }

        status
    }

    fn doFixedStep(&mut self) -> fmiStatus {
        let mut status = fmiOK;

        let communicationStepSize = self.system.fixedStepSize;

        let noSetFMUStatePriorToCurrentPoint = true;

        // Note: Direct parallelization of FMU instances is not possible due to
        // thread safety constraints (FMU callbacks are not Sync).
        // The FMU doStep calls must be executed sequentially.

        let currentCommunicationPoint = self.time;
        let communicationStepSize = self.system.fixedStepSize;

        let do_step = |instance: &FMUInstance<'_>| match instance {
            FMUInstance::FMI2(fmu) => {
                let status = fmu.doStep(currentCommunicationPoint, communicationStepSize, fmi2True);

                let mut terminated = fmi2False;

                if status == fmiDiscard {
                    fmu.getBooleanStatus(&fmi2StatusKind::fmi2Terminated, &mut terminated);
                }

                (status, terminated != fmi2False)
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
                (status, terminateSimulation)
            }
        };

        let result: Vec<(fmiStatus, bool)> = if self.system.parallelDoStep {
            self.instances.par_iter().map(do_step).collect()
        } else {
            self.instances.iter().map(do_step).collect()
        };

        for (do_step_status, terminated) in result {
            self.terminated |= terminated;
            if do_step_status > status {
                status = do_step_status;
            }
        }

        if !matches!(status, fmiOK | fmiWarning) || self.terminated {
            return status;
        }

        return_on_error!(status, self.updateConnections());

        self.time += communicationStepSize;

        status
    }

    fn doStep(
        &mut self,
        currentCommunicationPoint: fmiFloat64,
        communicationStepSize: fmiFloat64,
    ) -> fmiStatus {
        let mut status = fmiOK;

        if relative_ne!(currentCommunicationPoint, self.time) {
            let message = format!(
                "Expected currentCommunicationPoint={} but was {}",
                self.time, currentCommunicationPoint
            );
            self.logError(&message);
            return fmiError;
        }

        let next_time = currentCommunicationPoint + communicationStepSize;

        while self.time < next_time && relative_ne!(self.time, next_time) {
            return_on_error!(status, self.doFixedStep());
        }

        status
    }
}
