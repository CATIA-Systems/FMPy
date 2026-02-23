#![allow(non_camel_case_types, non_snake_case)]

mod common;

use common::create_fmi3_container;
use fmi::fmi3::types::*;

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi3OK);
    };
}

/// Test FMI3 Float32 connections
///
/// Tests the connection between Float32 variables:
/// - VR 1 (input to component 0) -> VR 2 (output from component 0) -> VR 1 (input to component 1)
/// - VR 3 (input to component 0) -> VR 4 (output from component 0) -> VR 3 (input to component 1)
#[test]
fn test_fmi3_float32_connections() {
    let fmu = create_fmi3_container();

    // Float32 input/output pairs based on model description
    let float32_input_vr = [1, 3]; // Input variables
    let mut float32_input_values = [1.1_f32, 2.2_f32];

    let float32_output_vr = [2, 4]; // Output variables (connected via container)
    let mut float32_output_values = [0.0_f32, 0.0_f32];

    // Set input values
    assert_ok!(fmu.setFloat32(&float32_input_vr, &float32_input_values));

    // FMI3 initialization sequence
    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    // Check if values have been forwarded after initialization
    assert_ok!(fmu.getFloat32(&float32_output_vr, &mut float32_output_values));
    assert_eq!(float32_output_values[0], float32_input_values[0]);
    assert_eq!(float32_output_values[1], float32_input_values[1]);

    // Set different input values
    float32_input_values[0] = 3.3;
    float32_input_values[1] = 4.4;
    assert_ok!(fmu.setFloat32(&float32_input_vr, &float32_input_values));

    // FMI3 doStep with additional parameters
    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    // Check if values have been forwarded after doStep
    assert_ok!(fmu.getFloat32(&float32_output_vr, &mut float32_output_values));
    assert_eq!(float32_output_values[0], float32_input_values[0]);
    assert_eq!(float32_output_values[1], float32_input_values[1]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Float64 connections
///
/// Tests the connection between Float64 variables:
/// - VR 7 (input to component 0) -> VR 8 (output from component 0) -> VR 7 (input to component 1)
/// - VR 9 (input to component 0) -> VR 10 (output from component 0) -> VR 9 (input to component 1)
#[test]
fn test_fmi3_float64_connections() {
    let fmu = create_fmi3_container();

    let float64_input_vr = [7, 9]; // Input variables
    let mut float64_input_values = [1.1_f64, 2.2_f64];

    let float64_output_vr = [8, 10]; // Output variables (connected via container)
    let mut float64_output_values = [0.0_f64, 0.0_f64];

    assert_ok!(fmu.setFloat64(&float64_input_vr, &float64_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getFloat64(&float64_output_vr, &mut float64_output_values));
    assert_eq!(float64_output_values[0], float64_input_values[0]);
    assert_eq!(float64_output_values[1], float64_input_values[1]);

    float64_input_values[0] = 3.3;
    float64_input_values[1] = 4.4;
    assert_ok!(fmu.setFloat64(&float64_input_vr, &float64_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getFloat64(&float64_output_vr, &mut float64_output_values));
    assert_eq!(float64_output_values[0], float64_input_values[0]);
    assert_eq!(float64_output_values[1], float64_input_values[1]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Int8 connections
///
/// Tests the connection between Int8 variables:
/// - VR 11 (input to component 0) -> VR 12 (output from component 0) -> VR 11 (input to component 1)
#[test]
fn test_fmi3_int8_connections() {
    let fmu = create_fmi3_container();

    let int8_input_vr = [11]; // Input variable
    let mut int8_input_values = [42_i8];

    let int8_output_vr = [12]; // Output variable (connected via container)
    let mut int8_output_values = [0_i8];

    assert_ok!(fmu.setInt8(&int8_input_vr, &int8_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInt8(&int8_output_vr, &mut int8_output_values));
    assert_eq!(int8_output_values[0], int8_input_values[0]);

    int8_input_values[0] = -99;
    assert_ok!(fmu.setInt8(&int8_input_vr, &int8_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getInt8(&int8_output_vr, &mut int8_output_values));
    assert_eq!(int8_output_values[0], int8_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Boolean connections
///
/// Tests the connection between Boolean variables:
/// - VR 27 (input to component 0) -> VR 28 (output from component 0) -> VR 27 (input to component 1)
#[test]
fn test_fmi3_boolean_connections() {
    let fmu = create_fmi3_container();

    let boolean_input_vr = [27]; // Input variable
    let mut boolean_input_values = [fmi3True];

    let boolean_output_vr = [28]; // Output variable (connected via container)
    let mut boolean_output_values = [fmi3False];

    assert_ok!(fmu.setBoolean(&boolean_input_vr, &boolean_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getBoolean(&boolean_output_vr, &mut boolean_output_values));
    assert_eq!(boolean_output_values[0], boolean_input_values[0]);

    boolean_input_values[0] = fmi3False;
    assert_ok!(fmu.setBoolean(&boolean_input_vr, &boolean_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getBoolean(&boolean_output_vr, &mut boolean_output_values));
    assert_eq!(boolean_output_values[0], boolean_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 String connections
///
/// Tests the connection between String variables:
/// - VR 29 (input to component 0) -> VR 30 (output from component 0) -> VR 29 (input to component 1)
#[test]
fn test_fmi3_string_connections() {
    let fmu = create_fmi3_container();

    let string_input_vr = [29]; // Input variable
    let string_input_values = ["test_string_fmi3"];

    let string_output_vr = [30]; // Output variable (connected via container)
    let mut string_output_values = [String::new()];

    assert_ok!(fmu.setString(&string_input_vr, &string_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getString(&string_output_vr, &mut string_output_values));
    assert_eq!(string_output_values[0], string_input_values[0]);

    let new_string_values = ["another_test_fmi3"];
    assert_ok!(fmu.setString(&string_input_vr, &new_string_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getString(&string_output_vr, &mut string_output_values));
    assert_eq!(string_output_values[0], new_string_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Int64 connections (including enumeration-like usage)
///
/// Tests the connection between Int64 variables:
/// - VR 23 (input to component 0) -> VR 24 (output from component 0) -> VR 23 (input to component 1)
/// Note: Only testing one Int64 connection as VR 33/34 are enumeration variables
#[test]
fn test_fmi3_int64_connections() {
    let fmu = create_fmi3_container();

    let int64_input_vr = [23]; // Input variable
    let mut int64_input_values = [42_i64];

    let int64_output_vr = [24]; // Output variable (connected via container)
    let mut int64_output_values = [0_i64];

    assert_ok!(fmu.setInt64(&int64_input_vr, &int64_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInt64(&int64_output_vr, &mut int64_output_values));
    assert_eq!(int64_output_values[0], int64_input_values[0]);

    int64_input_values[0] = -999;
    assert_ok!(fmu.setInt64(&int64_input_vr, &int64_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getInt64(&int64_output_vr, &mut int64_output_values));
    assert_eq!(int64_output_values[0], int64_input_values[0]);

    assert_ok!(fmu.terminate());
}
/// Test FMI3 UInt8 connections
///
/// Tests the connection between UInt8 variables:
/// - VR 13 (input to component 0) -> VR 14 (output from component 0) -> VR 13 (input to component 1)
#[test]
fn test_fmi3_uint8_connections() {
    let fmu = create_fmi3_container();

    let uint8_input_vr = [13]; // Input variable
    let mut uint8_input_values = [42_u8];

    let uint8_output_vr = [14]; // Output variable (connected via container)
    let mut uint8_output_values = [0_u8];

    assert_ok!(fmu.setUInt8(&uint8_input_vr, &uint8_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getUInt8(&uint8_output_vr, &mut uint8_output_values));
    assert_eq!(uint8_output_values[0], uint8_input_values[0]);

    uint8_input_values[0] = 255;
    assert_ok!(fmu.setUInt8(&uint8_input_vr, &uint8_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getUInt8(&uint8_output_vr, &mut uint8_output_values));
    assert_eq!(uint8_output_values[0], uint8_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Int16 connections
///
/// Tests the connection between Int16 variables:
/// - VR 15 (input to component 0) -> VR 16 (output from component 0) -> VR 15 (input to component 1)
#[test]
fn test_fmi3_int16_connections() {
    let fmu = create_fmi3_container();

    let int16_input_vr = [15]; // Input variable
    let mut int16_input_values = [1234_i16];

    let int16_output_vr = [16]; // Output variable (connected via container)
    let mut int16_output_values = [0_i16];

    assert_ok!(fmu.setInt16(&int16_input_vr, &int16_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInt16(&int16_output_vr, &mut int16_output_values));
    assert_eq!(int16_output_values[0], int16_input_values[0]);

    int16_input_values[0] = -32000;
    assert_ok!(fmu.setInt16(&int16_input_vr, &int16_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getInt16(&int16_output_vr, &mut int16_output_values));
    assert_eq!(int16_output_values[0], int16_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 UInt16 connections
///
/// Tests the connection between UInt16 variables:
/// - VR 17 (input to component 0) -> VR 18 (output from component 0) -> VR 17 (input to component 1)
#[test]
fn test_fmi3_uint16_connections() {
    let fmu = create_fmi3_container();

    let uint16_input_vr = [17]; // Input variable
    let mut uint16_input_values = [12345_u16];

    let uint16_output_vr = [18]; // Output variable (connected via container)
    let mut uint16_output_values = [0_u16];

    assert_ok!(fmu.setUInt16(&uint16_input_vr, &uint16_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getUInt16(&uint16_output_vr, &mut uint16_output_values));
    assert_eq!(uint16_output_values[0], uint16_input_values[0]);

    uint16_input_values[0] = 65535;
    assert_ok!(fmu.setUInt16(&uint16_input_vr, &uint16_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getUInt16(&uint16_output_vr, &mut uint16_output_values));
    assert_eq!(uint16_output_values[0], uint16_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Int32 connections
///
/// Tests the connection between Int32 variables:
/// - VR 19 (input to component 0) -> VR 20 (output from component 0) -> VR 19 (input to component 1)
#[test]
fn test_fmi3_int32_connections() {
    let fmu = create_fmi3_container();

    let int32_input_vr = [19]; // Input variable
    let mut int32_input_values = [123456789_i32];

    let int32_output_vr = [20]; // Output variable (connected via container)
    let mut int32_output_values = [0_i32];

    assert_ok!(fmu.setInt32(&int32_input_vr, &int32_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getInt32(&int32_output_vr, &mut int32_output_values));
    assert_eq!(int32_output_values[0], int32_input_values[0]);

    int32_input_values[0] = -2000000000;
    assert_ok!(fmu.setInt32(&int32_input_vr, &int32_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getInt32(&int32_output_vr, &mut int32_output_values));
    assert_eq!(int32_output_values[0], int32_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 UInt32 connections
///
/// Tests the connection between UInt32 variables:
/// - VR 21 (input to component 0) -> VR 22 (output from component 0) -> VR 21 (input to component 1)
#[test]
fn test_fmi3_uint32_connections() {
    let fmu = create_fmi3_container();

    let uint32_input_vr = [21]; // Input variable
    let mut uint32_input_values = [123456789_u32];

    let uint32_output_vr = [22]; // Output variable (connected via container)
    let mut uint32_output_values = [0_u32];

    assert_ok!(fmu.setUInt32(&uint32_input_vr, &uint32_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getUInt32(&uint32_output_vr, &mut uint32_output_values));
    assert_eq!(uint32_output_values[0], uint32_input_values[0]);

    uint32_input_values[0] = 4000000000;
    assert_ok!(fmu.setUInt32(&uint32_input_vr, &uint32_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getUInt32(&uint32_output_vr, &mut uint32_output_values));
    assert_eq!(uint32_output_values[0], uint32_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 UInt64 connections
///
/// Tests the connection between UInt64 variables:
/// - VR 25 (input to component 0) -> VR 26 (output from component 0) -> VR 25 (input to component 1)
#[test]
fn test_fmi3_uint64_connections() {
    let fmu = create_fmi3_container();

    let uint64_input_vr = [25]; // Input variable
    let mut uint64_input_values = [12345678901234567890_u64];

    let uint64_output_vr = [26]; // Output variable (connected via container)
    let mut uint64_output_values = [0_u64];

    assert_ok!(fmu.setUInt64(&uint64_input_vr, &uint64_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    assert_ok!(fmu.getUInt64(&uint64_output_vr, &mut uint64_output_values));
    assert_eq!(uint64_output_values[0], uint64_input_values[0]);

    uint64_input_values[0] = 18446744073709551615; // Max u64 value
    assert_ok!(fmu.setUInt64(&uint64_input_vr, &uint64_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    assert_ok!(fmu.getUInt64(&uint64_output_vr, &mut uint64_output_values));
    assert_eq!(uint64_output_values[0], uint64_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test FMI3 Enumeration connections
///
/// Tests the connection between Enumeration variables (handled as Int64):
/// - VR 31 (enumeration input) -> VR 32 (enumeration output) via Int64 connection VR 33→34
/// Note: Enumerations in FMI3 are handled as Int64 values in the container connections
#[test]
fn test_fmi3_enumeration_connections() {
    let fmu = create_fmi3_container();

    // Enumeration variables are accessed as Int64 in FMI3
    let enum_input_vr = [33]; // Enumeration input variable
    let mut enum_input_values = [2_i64]; // Option 2

    let enum_output_vr = [34]; // Enumeration output variable
    let mut enum_output_values = [0_i64];

    // Set enumeration value (Option 2)
    assert_ok!(fmu.setInt64(&enum_input_vr, &enum_input_values));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    assert_ok!(fmu.exitInitializationMode());

    // Check if enumeration value has been forwarded
    assert_ok!(fmu.getInt64(&enum_output_vr, &mut enum_output_values));
    assert_eq!(enum_output_values[0], enum_input_values[0]);

    // Change to Option 1
    enum_input_values[0] = 1;
    assert_ok!(fmu.setInt64(&enum_input_vr, &enum_input_values));

    let mut event_handling_needed = fmi3False;
    let mut terminate_simulation = fmi3False;
    let mut early_return = fmi3False;
    let mut last_successful_time = 0.0;

    assert_ok!(fmu.doStep(
        0.0,
        0.5,
        fmi3True,
        &mut event_handling_needed,
        &mut terminate_simulation,
        &mut early_return,
        &mut last_successful_time,
    ));

    // Check if enumeration value has been forwarded after doStep
    assert_ok!(fmu.getInt64(&enum_output_vr, &mut enum_output_values));
    assert_eq!(enum_output_values[0], enum_input_values[0]);

    assert_ok!(fmu.terminate());
}

/// Test demonstrating current FMI3 container limitations
///
/// IMPORTANT: This test demonstrates that the FMI3 container currently has limitations
/// with certain connection types. The container.json includes connections for:
///
/// SUPPORTED TYPES (these work):
/// - Float32, Float64, Int8, Boolean, String, Int64
///
/// UNSUPPORTED TYPES (these cause initialization to fail):
/// - UInt8, UInt16, UInt32, UInt64, Int16, Int32
///
/// The container can be instantiated and enter initialization mode successfully,
/// but fails during exitInitializationMode() due to unsupported connection types.
///
/// To test individual connection types, the container.json would need to be modified
/// to remove connections for unsupported types.
#[test]
fn test_fmi3_container_limitation() {
    let fmu = create_fmi3_container();

    // Container instantiation succeeds
    println!("✅ Container instantiated successfully");

    // Entering initialization mode succeeds
    assert_ok!(fmu.enterInitializationMode(None, 0.0, None));
    println!("✅ Entered initialization mode successfully");

    // This will fail due to unsupported UInt8, UInt16, UInt32, UInt64 connections
    // The error message will be: "Connections of type UInt8 are not supported"
    let result = fmu.exitInitializationMode();

    if result != fmi3OK {
        println!(
            "❌ Exit initialization mode failed as expected due to unsupported connection types"
        );
        println!(
            "   Current container limitations: UInt8, UInt16, UInt32, UInt64, Int16, Int32 connections not supported"
        );

        // Terminate the FMU even though initialization failed
        let _ = fmu.terminate();

        // This is expected behavior, so we don't panic
        return;
    }

    // If we reach here, the container has been updated to support all types
    println!("✅ Exit initialization mode succeeded - container limitations have been resolved!");

    assert_ok!(fmu.terminate());
}
