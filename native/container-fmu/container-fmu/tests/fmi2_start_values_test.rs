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

/// Test to verify that all start values defined in the container configuration
/// are correctly set when the container FMU is instantiated and initialized.
/// Note: Container start values override individual FMU model description start values.
#[test]
fn test_fmi2_start_values() {
    // Expected start values from container.json configuration
    // Only input variables and parameters have start values defined
    let expected_real_fixed_parameter = 1.0;      // container variable index 0: "start": ["1"]
    let expected_real_tunable_parameter = 2.0;    // container variable index 1: "start": ["2"]
    let expected_real_continuous_input = 3.0;     // container variable index 2: "start": ["3"]
    let expected_real_discrete_input = 5.0;       // container variable index 4: "start": ["5"]
    let expected_integer_input = 7;               // container variable index 6: "start": ["7"]
    let expected_boolean_input = fmi2True;        // container variable index 8: "start": ["true"]
    let expected_string_input = "container_string_1";  // container variable index 10: "start": ["container_string_1"]
    let expected_enumeration_input = 2;           // container variable index 12: "start": ["2"] (Option 2)

    // Value references from modelDescription.xml (only for variables with start values)
    let real_fixed_parameter_vr = [1];
    let real_tunable_parameter_vr = [2];
    let real_continuous_input_vr = [3];
    let real_discrete_input_vr = [5];
    let integer_input_vr = [7];
    let boolean_input_vr = [9];
    let string_input_vr = [11];
    let enumeration_input_vr = [13];

    // Output buffers (only for variables with start values)
    let mut real_fixed_parameter_values = [0.0];
    let mut real_tunable_parameter_values = [0.0];
    let mut real_continuous_input_values = [0.0];
    let mut real_discrete_input_values = [0.0];
    let mut integer_input_values = [0];
    let mut boolean_input_values = [fmi2False]; // Initialize to opposite of expected
    let mut string_input_values = [String::new()];
    let mut enumeration_input_values = [0];

    // Setup paths
    let resource_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("resources");

    let dll_prefix = if cfg!(windows) { "" } else { "lib" };
    let dll_path = format!("{}container_fmu{}", dll_prefix, SHARED_LIBRARY_EXTENSION);
    let dll_path = Path::new(&dll_path);

    // Setup logging callbacks
    let log_message = move |status: &fmi2Status, category: &str, message: &str| {
        println!("[{status:?}] [{category}] {message}")
    };

    let log_fmi_call = move |status: &fmi2Status, message: &str| {
        println!("[{status:?}] {message}")
    };

    // Create and initialize FMU
    let mut fmu = FMU2::new(
        dll_path,
        "main",
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    let resource_url = Url::from_directory_path(resource_path).unwrap();

    // Verify FMI version
    assert!(fmu.getVersion().starts_with("2."));

    // Instantiate the FMU
    assert_ok!(fmu.instantiate(
        "container",
        fmi2Type::fmi2CoSimulation,
        "f6cda2ea-6875-475c-b7dc-a43a33e69094",
        Some(&resource_url),
        false,
        true,
    ));

    // Setup experiment and enter initialization mode
    assert_ok!(fmu.setupExperiment(Some(1e-5), 0.0, Some(1.0)));
    assert_ok!(fmu.enterInitializationMode());

    // Test 1: Real fixed parameter (start="1")
    assert_ok!(fmu.getReal(&real_fixed_parameter_vr, &mut real_fixed_parameter_values));
    assert_eq!(
        real_fixed_parameter_values[0], 
        expected_real_fixed_parameter,
        "Real_fixed_parameter start value mismatch. Expected: {}, Got: {}",
        expected_real_fixed_parameter,
        real_fixed_parameter_values[0]
    );

    // Test 2: Real tunable parameter (start="2")
    assert_ok!(fmu.getReal(&real_tunable_parameter_vr, &mut real_tunable_parameter_values));
    assert_eq!(
        real_tunable_parameter_values[0], 
        expected_real_tunable_parameter,
        "Real_tunable_parameter start value mismatch. Expected: {}, Got: {}",
        expected_real_tunable_parameter,
        real_tunable_parameter_values[0]
    );

    // Test 3: Real continuous input (start="3")
    assert_ok!(fmu.getReal(&real_continuous_input_vr, &mut real_continuous_input_values));
    assert_eq!(
        real_continuous_input_values[0], 
        expected_real_continuous_input,
        "Real_continuous_input start value mismatch. Expected: {}, Got: {}",
        expected_real_continuous_input,
        real_continuous_input_values[0]
    );

    // Test 4: Real discrete input (start="5")
    assert_ok!(fmu.getReal(&real_discrete_input_vr, &mut real_discrete_input_values));
    assert_eq!(
        real_discrete_input_values[0], 
        expected_real_discrete_input,
        "Real_discrete_input start value mismatch. Expected: {}, Got: {}",
        expected_real_discrete_input,
        real_discrete_input_values[0]
    );

    // Test 5: Integer input (start="7")
    assert_ok!(fmu.getInteger(&integer_input_vr, &mut integer_input_values));
    assert_eq!(
        integer_input_values[0], 
        expected_integer_input,
        "Integer_input start value mismatch. Expected: {}, Got: {}",
        expected_integer_input,
        integer_input_values[0]
    );

    // Test 6: Boolean input (start="false")
    assert_ok!(fmu.getBoolean(&boolean_input_vr, &mut boolean_input_values));
    assert_eq!(
        boolean_input_values[0], 
        expected_boolean_input,
        "Boolean_input start value mismatch. Expected: {}, Got: {}",
        if expected_boolean_input == fmi2True { "true" } else { "false" },
        if boolean_input_values[0] == fmi2True { "true" } else { "false" }
    );

    // Test 7: String input (start="foo")
    assert_ok!(fmu.getString(&string_input_vr, &mut string_input_values));
    assert_eq!(
        string_input_values[0], 
        expected_string_input,
        "String_input start value mismatch. Expected: '{}', Got: '{}'",
        expected_string_input,
        string_input_values[0]
    );

    // Test 8: Enumeration input (start="2")
    assert_ok!(fmu.getInteger(&enumeration_input_vr, &mut enumeration_input_values));
    assert_eq!(
        enumeration_input_values[0], 
        expected_enumeration_input,
        "Enumeration_input start value mismatch. Expected: {} (Option 2), Got: {}",
        expected_enumeration_input,
        enumeration_input_values[0]
    );

    // Exit initialization mode to complete the test
    assert_ok!(fmu.exitInitializationMode());

    // Verify that start values are still correct after exiting initialization mode
    println!("Verifying start values after exiting initialization mode...");

    // Re-check a few key values to ensure they persist
    let mut recheck_real_values = [0.0];
    let mut recheck_integer_values = [0];
    let mut recheck_boolean_values = [fmi2False];
    let mut recheck_string_values = [String::new()];

    assert_ok!(fmu.getReal(&real_fixed_parameter_vr, &mut recheck_real_values));
    assert_eq!(recheck_real_values[0], expected_real_fixed_parameter);

    assert_ok!(fmu.getInteger(&integer_input_vr, &mut recheck_integer_values));
    assert_eq!(recheck_integer_values[0], expected_integer_input);

    assert_ok!(fmu.getBoolean(&boolean_input_vr, &mut recheck_boolean_values));
    assert_eq!(recheck_boolean_values[0], expected_boolean_input);

    assert_ok!(fmu.getString(&string_input_vr, &mut recheck_string_values));
    assert_eq!(recheck_string_values[0], expected_string_input);

    // Clean up
    assert_ok!(fmu.terminate());
    fmu.freeInstance();

    println!("✅ All input and parameter start values verified successfully!");
    println!("   Note: Output variables do not have start values as they are calculated from inputs.");
}

/// Test to verify that start values can be modified during initialization mode
/// and that the changes persist after exiting initialization mode.
#[test]
fn test_fmi2_start_values_modification() {
    // Setup paths
    let resource_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("resources");

    let dll_prefix = if cfg!(windows) { "" } else { "lib" };
    let dll_path = format!("{}container_fmu{}", dll_prefix, SHARED_LIBRARY_EXTENSION);
    let dll_path = Path::new(&dll_path);

    // Setup logging callbacks
    let log_message = move |status: &fmi2Status, category: &str, message: &str| {
        println!("[{status:?}] [{category}] {message}")
    };

    let log_fmi_call = move |status: &fmi2Status, message: &str| {
        println!("[{status:?}] {message}")
    };

    // Create and initialize FMU
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

    assert_ok!(fmu.setupExperiment(Some(1e-5), 0.0, Some(1.0)));
    assert_ok!(fmu.enterInitializationMode());

    // Test modifying tunable parameter during initialization
    let tunable_param_vr = [2];
    let new_tunable_value = [99.99];
    let mut retrieved_value = [0.0];

    // Set new value
    assert_ok!(fmu.setReal(&tunable_param_vr, &new_tunable_value));
    
    // Verify it was set
    assert_ok!(fmu.getReal(&tunable_param_vr, &mut retrieved_value));
    assert_eq!(retrieved_value[0], new_tunable_value[0]);

    // Test modifying input values during initialization
    let real_input_vr = [3];
    let new_real_input = [42.0];
    let mut retrieved_real_input = [0.0];

    assert_ok!(fmu.setReal(&real_input_vr, &new_real_input));
    assert_ok!(fmu.getReal(&real_input_vr, &mut retrieved_real_input));
    assert_eq!(retrieved_real_input[0], new_real_input[0]);

    let integer_input_vr = [7];
    let new_integer_input = [123];
    let mut retrieved_integer_input = [0];

    assert_ok!(fmu.setInteger(&integer_input_vr, &new_integer_input));
    assert_ok!(fmu.getInteger(&integer_input_vr, &mut retrieved_integer_input));
    assert_eq!(retrieved_integer_input[0], new_integer_input[0]);

    let boolean_input_vr = [9];
    let new_boolean_input = [fmi2True];
    let mut retrieved_boolean_input = [fmi2False];

    assert_ok!(fmu.setBoolean(&boolean_input_vr, &new_boolean_input));
    assert_ok!(fmu.getBoolean(&boolean_input_vr, &mut retrieved_boolean_input));
    assert_eq!(retrieved_boolean_input[0], new_boolean_input[0]);

    let string_input_vr = [11];
    let new_string_input = ["modified_string"];
    let mut retrieved_string_input = [String::new()];

    assert_ok!(fmu.setString(&string_input_vr, &new_string_input));
    assert_ok!(fmu.getString(&string_input_vr, &mut retrieved_string_input));
    assert_eq!(retrieved_string_input[0], new_string_input[0]);

    // Exit initialization mode
    assert_ok!(fmu.exitInitializationMode());

    // Verify that modified values persist after initialization
    let mut final_tunable_value = [0.0];
    let mut final_real_input = [0.0];
    let mut final_integer_input = [0];
    let mut final_boolean_input = [fmi2False];
    let mut final_string_input = [String::new()];

    assert_ok!(fmu.getReal(&tunable_param_vr, &mut final_tunable_value));
    assert_eq!(final_tunable_value[0], new_tunable_value[0]);

    assert_ok!(fmu.getReal(&real_input_vr, &mut final_real_input));
    assert_eq!(final_real_input[0], new_real_input[0]);

    assert_ok!(fmu.getInteger(&integer_input_vr, &mut final_integer_input));
    assert_eq!(final_integer_input[0], new_integer_input[0]);

    assert_ok!(fmu.getBoolean(&boolean_input_vr, &mut final_boolean_input));
    assert_eq!(final_boolean_input[0], new_boolean_input[0]);

    assert_ok!(fmu.getString(&string_input_vr, &mut final_string_input));
    assert_eq!(final_string_input[0], new_string_input[0]);

    // Clean up
    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}