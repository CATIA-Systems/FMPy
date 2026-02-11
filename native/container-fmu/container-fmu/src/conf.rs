use std::collections::HashSet;
use std::{fs::File, path::Path};

use serde::Deserialize;

use crate::VERSION;

#[derive(Debug, Deserialize, PartialEq)]
pub enum FMIMajorVersion {
    #[serde(rename = "2")]
    FMIMajorVersion2,
    #[serde(rename = "3")]
    FMIMajorVersion3,
}

#[derive(Debug, Deserialize, PartialEq)]
pub enum VariableType {
    Float32,
    Float64,
    Int8,
    UInt8,
    Int16,
    UInt16,
    Int32,
    UInt32,
    Int64,
    UInt64,
    Boolean,
    // Char,
    String,
    // Byte,
    Binary,
    Clock,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct System {
    pub containerVersion: String,
    pub instantiationToken: String,
    pub fixedStepSize: f64,
    pub parallelDoStep: bool,
    pub variables: Vec<Variable>,
    pub components: Vec<Component>,
    pub connections: Vec<Connection>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Mapping {
    pub component: u32,
    pub valueReference: u32,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Variable {
    pub variableType: VariableType,
    pub mappings: Vec<Mapping>,
    pub size: Option<usize>,
    pub start: Option<Vec<String>>,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Component {
    pub fmiMajorVersion: FMIMajorVersion,
    pub name: String,
    pub modelIdentifier: String,
    pub path: String,
    pub instantiationToken: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Connection {
    pub variableType: VariableType,
    pub srcComponent: usize,
    pub srcValueReferences: Vec<u32>,
    pub dstComponent: usize,
    pub dstValueReferences: Vec<u32>,
    pub size: Option<usize>,
}

impl System {
    pub fn from_path(config_path: &Path, instantiation_token: &str) -> Result<System, String> {
        let file = match File::open(&config_path) {
            Ok(f) => f,
            Err(_) => {
                let message = format!("Failed to open configuration file.");
                return Err(message);
            }
        };

        let system: System = match serde_json::from_reader(file) {
            Ok(s) => s,
            Err(error) => {
                let message = format!("Failed to parse configuration file: {error}");
                return Err(message);
            }
        };

        if system.containerVersion != VERSION {
            let message = format!(
                "Expected container version \"{}\" but was \"{}\".",
                VERSION, system.containerVersion
            );
            return Err(message);
        }

        if system.instantiationToken != instantiation_token {
            let message = format!(
                "Expected instantiation token \"{}\" but was \"{}\".",
                instantiation_token, system.instantiationToken
            );
            return Err(message);
        }

        if system.fixedStepSize < 0.0 {
            let message = format!("The fixed step size must be > 0 but was {}.", system.fixedStepSize);
            return Err(message);
        }

        for (i, variable) in system.variables.iter().enumerate() {
            // validate number of mappings
            if variable.mappings.is_empty() {
                let message = format!("Variable with index {i} has no mappings.");
                return Err(message.clone());
            }
            // validate component and value reference
            for (j, mapping) in variable.mappings.iter().enumerate() {
                if mapping.component as usize >= system.components.len() {
                    let message = format!(
                        "Mapping with index {j} in variable with index {i} has an invalid component index."
                    );
                    return Err(message.clone());
                }
            }
        }

        let mut instance_names = HashSet::new();

        // validate components
        for component in &system.components {
            if instance_names.contains(&component.name) {
                let message = format!("Component name \"{}\" is not unique.", component.name);
                return Err(message);
            } else {
                instance_names.insert(&component.name);
            }
        }

        Ok(system)
    }
}
