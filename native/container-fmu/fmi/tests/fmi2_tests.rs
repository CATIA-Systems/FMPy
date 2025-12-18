#![allow(non_camel_case_types, non_snake_case)]

use fmi::SHARED_LIBRARY_EXTENSION;
use fmi::fmi2::*;
use fmi::fmi2::{PLATFORM, types::*};
use fmi::types::fmiStatus;
use std::{env, path::PathBuf};
use url::Url;

macro_rules! assert_ok {
    ($status:expr) => {
        assert_eq!($status, fmi2OK);
    };
}

fn create_fmu() -> FMU2<'static> {
    let shared_library_name = format!("Feedthrough{SHARED_LIBRARY_EXTENSION}");

    let dll_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("Feedthrough")
        .join("binaries")
        .join(PLATFORM)
        .join(shared_library_name);

    let resource_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("Feedthrough")
        .join("resources");

    let log_message = move |status: &fmiStatus, category: &str, message: &str| {
        println!("[{status:?}] [{category}] {message}")
    };

    let log_fmi_call = move |status: &fmiStatus, message: &str| println!("[{status:?}] {message}");

    let mut fmu = FMU2::new(
        &dll_path,
        "main",
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    let resource_url = if resource_path.is_dir() {
        Some(Url::from_directory_path(&resource_path).unwrap())
    } else {
        None
    };

    assert_ok!(fmu.instantiate(
        "main",
        fmi2Type::fmi2CoSimulation,
        "{37B954F1-CC86-4D8F-B97F-C7C36F6670D2}",
        resource_url.as_ref(),
        false,
        true,
    ));

    let version = fmu.getVersion();
    assert!(version.starts_with("2."));

    assert_ok!(fmu.setupExperiment(None, 0.0, Some(1.0)));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    fmu
}

#[test]
fn test_real_continuous() {
    let mut fmu = create_fmu();

    let input_vr = [7];
    let input_values = [123.456789];

    let output_vr = [8];
    let mut output_values = [0.0];

    assert_ok!(fmu.setReal(&input_vr, &input_values));
    assert_ok!(fmu.getReal(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_real_discrete() {
    let mut fmu = create_fmu();

    let input_vr = [9];
    let input_values = [42.5];

    let output_vr = [10];
    let mut output_values = [0.0];

    assert_ok!(fmu.setReal(&input_vr, &input_values));
    assert_ok!(fmu.getReal(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_integer() {
    let mut fmu = create_fmu();

    let input_vr = [19];
    let input_values = [-987654321];

    let output_vr = [20];
    let mut output_values = [0];

    assert_ok!(fmu.setInteger(&input_vr, &input_values));
    assert_ok!(fmu.getInteger(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_boolean() {
    let mut fmu = create_fmu();

    let input_vr = [27];
    let input_values = [fmi2True];

    let output_vr = [28];
    let mut output_values = [fmi2False];

    assert_ok!(fmu.setBoolean(&input_vr, &input_values));
    assert_ok!(fmu.getBoolean(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    // Test with false value
    let input_values_false = [fmi2False];
    let mut output_values_false = [fmi2True];

    assert_ok!(fmu.setBoolean(&input_vr, &input_values_false));
    assert_ok!(fmu.getBoolean(&output_vr, &mut output_values_false));
    assert_eq!(output_values_false, input_values_false);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_string() {
    let mut fmu = create_fmu();

    let input_vr = [29];
    let input_values = ["Hello, FMI2!"];

    let output_vr = [30];
    let mut output_values = [String::new()];

    assert_ok!(fmu.setString(&input_vr, &input_values));
    assert_ok!(fmu.getString(&output_vr, &mut output_values));

    assert_eq!(output_values[0], input_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_enumeration() {
    let mut fmu = create_fmu();

    let input_vr = [33];
    let input_values = [2]; // Option 2

    let output_vr = [34];
    let mut output_values = [0];

    assert_ok!(fmu.setInteger(&input_vr, &input_values));
    assert_ok!(fmu.getInteger(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    // Test with Option 1
    let input_values_option1 = [1];
    let mut output_values_option1 = [0];

    assert_ok!(fmu.setInteger(&input_vr, &input_values_option1));
    assert_ok!(fmu.getInteger(&output_vr, &mut output_values_option1));
    assert_eq!(output_values_option1, input_values_option1);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_multiple_variables() {
    let mut fmu = create_fmu();

    // Test setting and getting multiple different variable types in one test

    // Real
    let real_input_vr = [7];
    let real_input_values = [123.456];
    let real_output_vr = [8];
    let mut real_output_values = [0.0];

    // Integer
    let int_input_vr = [19];
    let int_input_values = [42];
    let int_output_vr = [20];
    let mut int_output_values = [0];

    // Boolean
    let bool_input_vr = [27];
    let bool_input_values = [fmi2True];
    let bool_output_vr = [28];
    let mut bool_output_values = [fmi2False];

    // String
    let string_input_vr = [29];
    let string_input_values = ["Multi-test"];
    let string_output_vr = [30];
    let mut string_output_values = [String::new()];

    // Set all input values
    assert_ok!(fmu.setReal(&real_input_vr, &real_input_values));
    assert_ok!(fmu.setInteger(&int_input_vr, &int_input_values));
    assert_ok!(fmu.setBoolean(&bool_input_vr, &bool_input_values));
    assert_ok!(fmu.setString(&string_input_vr, &string_input_values));

    // Get all output values
    assert_ok!(fmu.getReal(&real_output_vr, &mut real_output_values));
    assert_ok!(fmu.getInteger(&int_output_vr, &mut int_output_values));
    assert_ok!(fmu.getBoolean(&bool_output_vr, &mut bool_output_values));
    assert_ok!(fmu.getString(&string_output_vr, &mut string_output_values));

    // Verify all values
    assert_eq!(real_output_values, real_input_values);
    assert_eq!(int_output_values, int_input_values);
    assert_eq!(bool_output_values, bool_input_values);
    assert_eq!(string_output_values[0], string_input_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_edge_cases() {
    let mut fmu = create_fmu();

    // Test extreme values for different types

    // Real edge cases
    let real_input_vr = [7];
    let real_output_vr = [8];

    // Test positive infinity
    let pos_inf = [f64::INFINITY];
    let mut output = [0.0];
    assert_ok!(fmu.setReal(&real_input_vr, &pos_inf));
    assert_ok!(fmu.getReal(&real_output_vr, &mut output));
    assert!(output[0].is_infinite() && output[0].is_sign_positive());

    // Test negative infinity
    let neg_inf = [f64::NEG_INFINITY];
    assert_ok!(fmu.setReal(&real_input_vr, &neg_inf));
    assert_ok!(fmu.getReal(&real_output_vr, &mut output));
    assert!(output[0].is_infinite() && output[0].is_sign_negative());

    // Test NaN
    let nan = [f64::NAN];
    assert_ok!(fmu.setReal(&real_input_vr, &nan));
    assert_ok!(fmu.getReal(&real_output_vr, &mut output));
    assert!(output[0].is_nan());

    // Test minimum and maximum integer values
    let int_input_vr = [19];
    let int_output_vr = [20];

    let max_int = [i32::MAX];
    let mut int_output = [0];
    assert_ok!(fmu.setInteger(&int_input_vr, &max_int));
    assert_ok!(fmu.getInteger(&int_output_vr, &mut int_output));
    assert_eq!(int_output, max_int);

    let min_int = [i32::MIN];
    assert_ok!(fmu.setInteger(&int_input_vr, &min_int));
    assert_ok!(fmu.getInteger(&int_output_vr, &mut int_output));
    assert_eq!(int_output, min_int);

    // Test very small and very large real numbers
    let very_small = [f64::MIN_POSITIVE];
    assert_ok!(fmu.setReal(&real_input_vr, &very_small));
    assert_ok!(fmu.getReal(&real_output_vr, &mut output));
    assert_eq!(output, very_small);

    let very_large = [f64::MAX];
    assert_ok!(fmu.setReal(&real_input_vr, &very_large));
    assert_ok!(fmu.getReal(&real_output_vr, &mut output));
    assert_eq!(output, very_large);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_parameters() {
    let mut fmu = create_fmu();

    // Test fixed parameter (should be settable during initialization)
    let fixed_param_vr = [5];
    let fixed_param_values = [3.14159];
    let mut output_values = [0.0];

    // Set parameter value
    assert_ok!(fmu.setReal(&fixed_param_vr, &fixed_param_values));
    assert_ok!(fmu.getReal(&fixed_param_vr, &mut output_values));
    assert_eq!(output_values, fixed_param_values);

    // Test tunable parameter
    let tunable_param_vr = [6];
    let tunable_param_values = [2.71828];
    let mut tunable_output_values = [0.0];

    assert_ok!(fmu.setReal(&tunable_param_vr, &tunable_param_values));
    assert_ok!(fmu.getReal(&tunable_param_vr, &mut tunable_output_values));
    assert_eq!(tunable_output_values, tunable_param_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_simulation_step() {
    let mut fmu = create_fmu();

    // Set some input values
    let real_input_vr = [7];
    let real_input_values = [1.0];
    let int_input_vr = [19];
    let int_input_values = [100];

    assert_ok!(fmu.setReal(&real_input_vr, &real_input_values));
    assert_ok!(fmu.setInteger(&int_input_vr, &int_input_values));

    // Perform a simulation step
    let current_time = 0.0;
    let step_size = 0.1;
    assert_ok!(fmu.doStep(current_time, step_size, fmi2True));

    // Check that outputs are still correct after the step
    let real_output_vr = [8];
    let mut real_output_values = [0.0];
    let int_output_vr = [20];
    let mut int_output_values = [0];

    assert_ok!(fmu.getReal(&real_output_vr, &mut real_output_values));
    assert_ok!(fmu.getInteger(&int_output_vr, &mut int_output_values));

    assert_eq!(real_output_values, real_input_values);
    assert_eq!(int_output_values, int_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_empty_string() {
    let mut fmu = create_fmu();

    let input_vr = [29];
    let input_values = [""];

    let output_vr = [30];
    let mut output_values = [String::new()];

    assert_ok!(fmu.setString(&input_vr, &input_values));
    assert_ok!(fmu.getString(&output_vr, &mut output_values));

    assert_eq!(output_values[0], input_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_long_string() {
    let mut fmu = create_fmu();

    let input_vr = [29];
    // Use a string that's within the 128 byte limit
    let long_string = "This is a long string that tests FMI2 string handling with special symbols: !@#$%^&*()_+-=[]{}|;':\",./<>?";
    let input_values = [long_string];

    let output_vr = [30];
    let mut output_values = [String::new()];

    assert_ok!(fmu.setString(&input_vr, &input_values));
    assert_ok!(fmu.getString(&output_vr, &mut output_values));

    assert_eq!(output_values[0], input_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_zero_values() {
    let mut fmu = create_fmu();

    // Test zero real value
    let real_input_vr = [7];
    let real_input_values = [0.0];
    let real_output_vr = [8];
    let mut real_output_values = [1.0]; // Non-zero initial value

    assert_ok!(fmu.setReal(&real_input_vr, &real_input_values));
    assert_ok!(fmu.getReal(&real_output_vr, &mut real_output_values));
    assert_eq!(real_output_values, real_input_values);

    // Test zero integer value
    let int_input_vr = [19];
    let int_input_values = [0];
    let int_output_vr = [20];
    let mut int_output_values = [42]; // Non-zero initial value

    assert_ok!(fmu.setInteger(&int_input_vr, &int_input_values));
    assert_ok!(fmu.getInteger(&int_output_vr, &mut int_output_values));
    assert_eq!(int_output_values, int_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_string_length_limit() {
    let mut fmu = create_fmu();

    let input_vr = [29];
    // Create a string that exceeds the 128 byte limit
    let too_long_string = "A".repeat(200);
    let input_values = [too_long_string.as_str()];

    // This should return an error due to string length limit
    let result = fmu.setString(&input_vr, &input_values);
    assert_eq!(result, fmi2Error);

    // Don't call terminate after an error - the FMU may be in an invalid state
    // Just free the instance directly
    fmu.freeInstance();
}
