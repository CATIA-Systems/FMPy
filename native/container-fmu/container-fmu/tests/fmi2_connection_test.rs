#![allow(non_camel_case_types, non_snake_case)]

use fmi::fmi2::types::*;
use fmi::{SHARED_LIBRARY_EXTENSION, fmi2::*};
use std::{
    env,
    path::{Path, PathBuf},
};
use url::Url;

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi2OK);
    };
}

fn create_fmu() -> FMU2<'static> {
    let resource_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("resources");

    let dll_prefix = if cfg!(windows) { "" } else { "lib" };
    let dll_path = format!("{}container_fmu{}", dll_prefix, SHARED_LIBRARY_EXTENSION);
    let dll_path = Path::new(&dll_path);

    let log_message = move |status: &fmi2Status, category: &str, message: &str| {
        println!(" [{status:?}] [{category}] {message}")
    };

    let log_fmi_call =
        move |status: &fmi2Status, message: &str| println!(">[{status:?}] {message}");

    let mut fmu = FMU2::new(
        dll_path,
        "main",
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    let resource_url = Url::from_directory_path(resource_path).unwrap();

    assert_ok!(fmu.instantiate(
        "container",
        fmi2Type::fmi2CoSimulation,
        "f6cda2ea-6875-475c-b7dc-a43a33e69094",
        Some(&resource_url),
        false,
        true,
    ));

    fmu
}

#[test]
fn test_fmi2_real_continuous_connections() {
    let mut fmu = create_fmu();

    let Real_continuous_input_vr = [3];
    let mut Real_continuous_input_values = [1.1];

    let Real_continuous_output_vr = [4];
    let mut Real_continuous_output_values = [0.0];

    // set an input value
    assert_ok!(fmu.setReal(&Real_continuous_input_vr, &Real_continuous_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    // check if the value has been forwarded after exiting intialization mode
    assert_ok!(fmu.getReal(
        &Real_continuous_output_vr,
        &mut Real_continuous_output_values
    ));
    assert_eq!(Real_continuous_output_values, Real_continuous_input_values);

    // set a different input value
    Real_continuous_input_values[0] = 1.2;
    assert_ok!(fmu.setReal(&Real_continuous_input_vr, &Real_continuous_input_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    // check if the value has been forwarded after the doStep
    assert_ok!(fmu.getReal(
        &Real_continuous_output_vr,
        &mut Real_continuous_output_values
    ));
    assert_eq!(Real_continuous_output_values, Real_continuous_input_values);

    assert_ok!(fmu.terminate());

    fmu.freeInstance();
}

#[test]
fn test_fmi2_real_discrete_connections() {
    let mut fmu = create_fmu();

    let Real_discrete_input_vr = [5];
    let mut Real_discrete_input_values = [2.5];

    let Real_discrete_output_vr = [6];
    let mut Real_discrete_output_values = [0.0];

    assert_ok!(fmu.setReal(&Real_discrete_input_vr, &Real_discrete_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getReal(&Real_discrete_output_vr, &mut Real_discrete_output_values));
    assert_eq!(Real_discrete_output_values, Real_discrete_input_values);

    Real_discrete_input_values[0] = 3.7;
    assert_ok!(fmu.setReal(&Real_discrete_input_vr, &Real_discrete_input_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    assert_ok!(fmu.getReal(&Real_discrete_output_vr, &mut Real_discrete_output_values));
    assert_eq!(Real_discrete_output_values, Real_discrete_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_fmi2_integer_connections() {
    let mut fmu = create_fmu();

    let Integer_input_vr = [7];
    let mut Integer_input_values = [42];

    let Integer_output_vr = [8];
    let mut Integer_output_values = [0];

    assert_ok!(fmu.setInteger(&Integer_input_vr, &Integer_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInteger(&Integer_output_vr, &mut Integer_output_values));
    assert_eq!(Integer_output_values, Integer_input_values);

    Integer_input_values[0] = -999;
    assert_ok!(fmu.setInteger(&Integer_input_vr, &Integer_input_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    assert_ok!(fmu.getInteger(&Integer_output_vr, &mut Integer_output_values));
    assert_eq!(Integer_output_values, Integer_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_fmi2_boolean_connections() {
    let mut fmu = create_fmu();

    let Boolean_input_vr = [9];
    let mut Boolean_input_values = [fmi2True];

    let Boolean_output_vr = [10];
    let mut Boolean_output_values = [fmi2False];

    assert_ok!(fmu.setBoolean(&Boolean_input_vr, &Boolean_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getBoolean(&Boolean_output_vr, &mut Boolean_output_values));
    assert_eq!(Boolean_output_values, Boolean_input_values);

    Boolean_input_values[0] = fmi2False;
    assert_ok!(fmu.setBoolean(&Boolean_input_vr, &Boolean_input_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    assert_ok!(fmu.getBoolean(&Boolean_output_vr, &mut Boolean_output_values));
    assert_eq!(Boolean_output_values, Boolean_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_fmi2_string_connections() {
    let mut fmu = create_fmu();

    let String_input_vr = [11];
    let String_input_values = ["test_string"];

    let String_output_vr = [12];
    let mut String_output_values = [String::new()];

    assert_ok!(fmu.setString(&String_input_vr, &String_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getString(&String_output_vr, &mut String_output_values));
    assert_eq!(String_output_values[0], String_input_values[0]);

    let new_string_values = ["another_test"];
    assert_ok!(fmu.setString(&String_input_vr, &new_string_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    assert_ok!(fmu.getString(&String_output_vr, &mut String_output_values));
    assert_eq!(String_output_values[0], new_string_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_fmi2_enumeration_connections() {
    let mut fmu = create_fmu();

    let Enumeration_input_vr = [13];
    let mut Enumeration_input_values = [1]; // Option 1

    let Enumeration_output_vr = [14];
    let mut Enumeration_output_values = [0];

    assert_ok!(fmu.setInteger(&Enumeration_input_vr, &Enumeration_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInteger(&Enumeration_output_vr, &mut Enumeration_output_values));
    assert_eq!(Enumeration_output_values, Enumeration_input_values);

    Enumeration_input_values[0] = 2; // Option 2
    assert_ok!(fmu.setInteger(&Enumeration_input_vr, &Enumeration_input_values));

    assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    assert_ok!(fmu.getInteger(&Enumeration_output_vr, &mut Enumeration_output_values));
    assert_eq!(Enumeration_output_values, Enumeration_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}
