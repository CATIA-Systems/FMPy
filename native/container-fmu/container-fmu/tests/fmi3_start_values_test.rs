#![allow(non_camel_case_types, non_snake_case)]

use fmi::fmi3::types::*;
use fmi::{SHARED_LIBRARY_EXTENSION, fmi3::*};
use std::{
    env,
    path::{Path, PathBuf},
};

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi3OK);
    };
}

/// Test to verify that all start values defined in the FMI3 container configuration
/// are correctly set when the container FMU is instantiated and initialized.
/// Note: Container start values override individual FMU model description start values.
#[test]
fn test_fmi3_start_values() {
    // Expected start values from container.json configuration
    // Only input variables and parameters have start values defined
    let expected_float32_continuous_input = 1.5f32; // container variable index 0: "start": ["1.5"]
    let expected_float32_discrete_input = 3.5f32; // container variable index 2: "start": ["3.5"]
    let expected_float64_fixed_parameter = 5.0; // container variable index 4: "start": ["5.0"]
    let expected_float64_tunable_parameter = 6.0; // container variable index 5: "start": ["6.0"]
    let expected_float64_continuous_input = 7.0; // container variable index 6: "start": ["7.0"]
    let expected_float64_discrete_input = 9.0; // container variable index 8: "start": ["9.0"]
    let expected_int8_input = 11i8; // container variable index 10: "start": ["11"]
    let expected_uint8_input = 13u8; // container variable index 12: "start": ["13"]
    let expected_int16_input = 15i16; // container variable index 14: "start": ["15"]
    let expected_uint16_input = 17u16; // container variable index 16: "start": ["17"]
    let expected_int32_input = 19i32; // container variable index 18: "start": ["19"]
    let expected_uint32_input = 21u32; // container variable index 20: "start": ["21"]
    let expected_int64_input = 23i64; // container variable index 22: "start": ["23"]
    let expected_uint64_input = 25u64; // container variable index 24: "start": ["25"]
    let expected_boolean_input = true; // container variable index 26: "start": ["true"]
    let expected_string_input = "container_fmi3_string"; // container variable index 28: "start": ["container_fmi3_string"]

    let expected_enumeration_input = 2i64; // container variable index 32: "start": ["2"] (Option 2)

    // Value references from modelDescription.xml (only for variables with start values)
    let float32_continuous_input_vr = [1];
    let float32_discrete_input_vr = [3];
    let float64_fixed_parameter_vr = [5];
    let float64_tunable_parameter_vr = [6];
    let float64_continuous_input_vr = [7];
    let float64_discrete_input_vr = [9];
    let int8_input_vr = [11];
    let uint8_input_vr = [13];
    let int16_input_vr = [15];
    let uint16_input_vr = [17];
    let int32_input_vr = [19];
    let uint32_input_vr = [21];
    let int64_input_vr = [23];
    let uint64_input_vr = [25];
    let boolean_input_vr = [27];
    let string_input_vr = [29];

    let enumeration_input_vr = [31];

    // Output buffers (only for variables with start values)
    let mut float32_continuous_input_values = [0.0f32];
    let mut float32_discrete_input_values = [0.0f32];
    let mut float64_fixed_parameter_values = [0.0];
    let mut float64_tunable_parameter_values = [0.0];
    let mut float64_continuous_input_values = [0.0];
    let mut float64_discrete_input_values = [0.0];
    let mut int8_input_values = [0i8];
    let mut uint8_input_values = [0u8];
    let mut int16_input_values = [0i16];
    let mut uint16_input_values = [0u16];
    let mut int32_input_values = [0i32];
    let mut uint32_input_values = [0u32];
    let mut int64_input_values = [0i64];
    let mut uint64_input_values = [0u64];
    let mut boolean_input_values = [false]; // Initialize to opposite of expected
    let mut string_input_values = [String::new()];

    let mut enumeration_input_values = [0i64];

    // Setup paths
    let resource_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi3")
        .join("resources");

    let dll_prefix = if cfg!(windows) { "" } else { "lib" };
    let dll_path = format!("{}container_fmu{}", dll_prefix, SHARED_LIBRARY_EXTENSION);
    let dll_path = Path::new(&dll_path);

    // Setup logging callbacks
    let log_message = move |status: &fmi3Status, category: &str, message: &str| {
        println!(" [{status:?}] [{category}] {message}")
    };

    let log_fmi_call =
        move |status: &fmi3Status, message: &str| println!(">[{status:?}] {message}");

    // Create and initialize FMU
    let mut fmu = FMU3::new(
        dll_path,
        "main",
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    // Verify FMI version
    assert!(fmu.getVersion().starts_with("3."));

    // Instantiate the FMU
    assert_ok!(fmu.instantiateCoSimulation(
        "container",
        "{088cfe7e-cb81-4ca1-a83d-e7a5c3ff47fd}",
        Some(resource_path.as_path()),
        false,
        true,
        false,
        false,
        &[],
    ));

    // Setup experiment and enter initialization mode
    assert_ok!(fmu.enterInitializationMode(Some(1e-5), 0.0, Some(1.0)));

    // Test 1: Float32 continuous input (start="1.5")
    assert_ok!(fmu.getFloat32(
        &float32_continuous_input_vr,
        &mut float32_continuous_input_values
    ));
    assert_eq!(
        float32_continuous_input_values[0], expected_float32_continuous_input,
        "Float32_continuous_input start value mismatch. Expected: {}, Got: {}",
        expected_float32_continuous_input, float32_continuous_input_values[0]
    );

    // Test 2: Float32 discrete input (start="3.5")
    assert_ok!(fmu.getFloat32(
        &float32_discrete_input_vr,
        &mut float32_discrete_input_values
    ));
    assert_eq!(
        float32_discrete_input_values[0], expected_float32_discrete_input,
        "Float32_discrete_input start value mismatch. Expected: {}, Got: {}",
        expected_float32_discrete_input, float32_discrete_input_values[0]
    );

    // Test 3: Float64 fixed parameter (start="5.0")
    assert_ok!(fmu.getFloat64(
        &float64_fixed_parameter_vr,
        &mut float64_fixed_parameter_values
    ));
    assert_eq!(
        float64_fixed_parameter_values[0], expected_float64_fixed_parameter,
        "Float64_fixed_parameter start value mismatch. Expected: {}, Got: {}",
        expected_float64_fixed_parameter, float64_fixed_parameter_values[0]
    );

    // Test 4: Float64 tunable parameter (start="6.0")
    assert_ok!(fmu.getFloat64(
        &float64_tunable_parameter_vr,
        &mut float64_tunable_parameter_values
    ));
    assert_eq!(
        float64_tunable_parameter_values[0], expected_float64_tunable_parameter,
        "Float64_tunable_parameter start value mismatch. Expected: {}, Got: {}",
        expected_float64_tunable_parameter, float64_tunable_parameter_values[0]
    );

    // Test 5: Float64 continuous input (start="7.0")
    assert_ok!(fmu.getFloat64(
        &float64_continuous_input_vr,
        &mut float64_continuous_input_values
    ));
    assert_eq!(
        float64_continuous_input_values[0], expected_float64_continuous_input,
        "Float64_continuous_input start value mismatch. Expected: {}, Got: {}",
        expected_float64_continuous_input, float64_continuous_input_values[0]
    );

    // Test 6: Float64 discrete input (start="9.0")
    assert_ok!(fmu.getFloat64(
        &float64_discrete_input_vr,
        &mut float64_discrete_input_values
    ));
    assert_eq!(
        float64_discrete_input_values[0], expected_float64_discrete_input,
        "Float64_discrete_input start value mismatch. Expected: {}, Got: {}",
        expected_float64_discrete_input, float64_discrete_input_values[0]
    );

    // Test 7: Int8 input (start="11")
    assert_ok!(fmu.getInt8(&int8_input_vr, &mut int8_input_values));
    assert_eq!(
        int8_input_values[0], expected_int8_input,
        "Int8_input start value mismatch. Expected: {}, Got: {}",
        expected_int8_input, int8_input_values[0]
    );

    // Test 8: UInt8 input (start="13")
    assert_ok!(fmu.getUInt8(&uint8_input_vr, &mut uint8_input_values));
    assert_eq!(
        uint8_input_values[0], expected_uint8_input,
        "UInt8_input start value mismatch. Expected: {}, Got: {}",
        expected_uint8_input, uint8_input_values[0]
    );

    // Test 9: Int16 input (start="15")
    assert_ok!(fmu.getInt16(&int16_input_vr, &mut int16_input_values));
    assert_eq!(
        int16_input_values[0], expected_int16_input,
        "Int16_input start value mismatch. Expected: {}, Got: {}",
        expected_int16_input, int16_input_values[0]
    );

    // Test 10: UInt16 input (start="17")
    assert_ok!(fmu.getUInt16(&uint16_input_vr, &mut uint16_input_values));
    assert_eq!(
        uint16_input_values[0], expected_uint16_input,
        "UInt16_input start value mismatch. Expected: {}, Got: {}",
        expected_uint16_input, uint16_input_values[0]
    );

    // Test 11: Int32 input (start="19")
    assert_ok!(fmu.getInt32(&int32_input_vr, &mut int32_input_values));
    assert_eq!(
        int32_input_values[0], expected_int32_input,
        "Int32_input start value mismatch. Expected: {}, Got: {}",
        expected_int32_input, int32_input_values[0]
    );

    // Test 12: UInt32 input (start="21")
    assert_ok!(fmu.getUInt32(&uint32_input_vr, &mut uint32_input_values));
    assert_eq!(
        uint32_input_values[0], expected_uint32_input,
        "UInt32_input start value mismatch. Expected: {}, Got: {}",
        expected_uint32_input, uint32_input_values[0]
    );

    // Test 13: Int64 input (start="23")
    assert_ok!(fmu.getInt64(&int64_input_vr, &mut int64_input_values));
    assert_eq!(
        int64_input_values[0], expected_int64_input,
        "Int64_input start value mismatch. Expected: {}, Got: {}",
        expected_int64_input, int64_input_values[0]
    );

    // Test 14: UInt64 input (start="25")
    assert_ok!(fmu.getUInt64(&uint64_input_vr, &mut uint64_input_values));
    assert_eq!(
        uint64_input_values[0], expected_uint64_input,
        "UInt64_input start value mismatch. Expected: {}, Got: {}",
        expected_uint64_input, uint64_input_values[0]
    );

    // Test 15: Boolean input (start="true")
    assert_ok!(fmu.getBoolean(&boolean_input_vr, &mut boolean_input_values));
    assert_eq!(
        boolean_input_values[0], expected_boolean_input,
        "Boolean_input start value mismatch. Expected: {}, Got: {}",
        expected_boolean_input, boolean_input_values[0]
    );

    // Test 16: String input (start="container_fmi3_string")
    assert_ok!(fmu.getString(&string_input_vr, &mut string_input_values));
    assert_eq!(
        string_input_values[0], expected_string_input,
        "String_input start value mismatch. Expected: '{}', Got: '{}'",
        expected_string_input, string_input_values[0]
    );

    // Test 18: Enumeration input (start="2")
    assert_ok!(fmu.getInt64(&enumeration_input_vr, &mut enumeration_input_values));
    assert_eq!(
        enumeration_input_values[0], expected_enumeration_input,
        "Enumeration_input start value mismatch. Expected: {} (Option 2), Got: {}",
        expected_enumeration_input, enumeration_input_values[0]
    );

    // Exit initialization mode to complete the test
    assert_ok!(fmu.exitInitializationMode());

    // Clean up
    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}
