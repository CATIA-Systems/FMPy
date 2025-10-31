#![allow(non_camel_case_types, non_snake_case)]

use fmi::SHARED_LIBRARY_EXTENSION;
use fmi::fmi3::*;
use fmi::fmi3::{PLATFORM_TUPLE, types::*};
use fmi::types::fmiStatus;
use std::{env, path::PathBuf};

macro_rules! assert_ok {
    ($status:expr) => {
        assert_eq!($status, fmi3OK);
    };
}

fn create_fmu() -> FMU3<'static> {
    let shared_library_name = format!("Feedthrough{SHARED_LIBRARY_EXTENSION}");

    let dll_path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("resources")
        .join("fmi3")
        .join("Feedthrough")
        .join("binaries")
        .join(PLATFORM_TUPLE)
        .join(shared_library_name);

    let log_message = move |status: &fmiStatus, category: &str, message: &str| {
        println!("[{status:?}] [{category}] {message}")
    };

    let log_fmi_call = move |status: &fmiStatus, message: &str| println!("[{status:?}] {message}");

    let mut fmu = FMU3::new(
        &dll_path,
        "main",
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    assert_ok!(fmu.instantiateCoSimulation(
        "main",
        "{37B954F1-CC86-4D8F-B97F-C7C36F6670D2}",
        None,
        false,
        true,
        false,
        false,
        &[]
    ));

    let version = fmu.getVersion();
    assert!(version.starts_with("3."));

    assert_ok!(fmu.enterInitializationMode(None, 0.0, Some(1.0)));
    assert_ok!(fmu.exitInitializationMode());

    fmu
}

#[test]
fn test_float32() {
    let mut fmu = create_fmu();

    let input_vr = [1];
    let input_values = [42.5f32];

    let output_vr = [2];
    let mut output_values = [0f32];

    assert_ok!(fmu.setFloat32(&input_vr, &input_values));
    assert_ok!(fmu.getFloat32(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_float64() {
    let mut fmu = create_fmu();

    let input_vr = [7];
    let input_values = [123.456789];

    let output_vr = [8];
    let mut output_values = [0.0];

    assert_ok!(fmu.setFloat64(&input_vr, &input_values));
    assert_ok!(fmu.getFloat64(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_int8() {
    let mut fmu = create_fmu();

    let input_vr = [11];
    let input_values = [42i8];

    let output_vr = [12];
    let mut output_values = [0i8];

    assert_ok!(fmu.setInt8(&input_vr, &input_values));
    assert_ok!(fmu.getInt8(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_uint8() {
    let mut fmu = create_fmu();

    let input_vr = [13];
    let input_values = [200u8];

    let output_vr = [14];
    let mut output_values = [0u8];

    assert_ok!(fmu.setUInt8(&input_vr, &input_values));
    assert_ok!(fmu.getUInt8(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_int16() {
    let mut fmu = create_fmu();

    let input_vr = [15];
    let input_values = [-12345i16];

    let output_vr = [16];
    let mut output_values = [0i16];

    assert_ok!(fmu.setInt16(&input_vr, &input_values));
    assert_ok!(fmu.getInt16(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_uint16() {
    let mut fmu = create_fmu();

    let input_vr = [17];
    let input_values = [54321u16];

    let output_vr = [18];
    let mut output_values = [0u16];

    assert_ok!(fmu.setUInt16(&input_vr, &input_values));
    assert_ok!(fmu.getUInt16(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_int32() {
    let mut fmu = create_fmu();

    let input_vr = [19];
    let input_values = [-987654321i32];

    let output_vr = [20];
    let mut output_values = [0i32];

    assert_ok!(fmu.setInt32(&input_vr, &input_values));
    assert_ok!(fmu.getInt32(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_uint32() {
    let mut fmu = create_fmu();

    let input_vr = [21];
    let input_values = [3000000000u32];

    let output_vr = [22];
    let mut output_values = [0u32];

    assert_ok!(fmu.setUInt32(&input_vr, &input_values));
    assert_ok!(fmu.getUInt32(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_int64() {
    let mut fmu = create_fmu();

    let input_vr = [23];
    let input_values = [-9223372036854775807i64];

    let output_vr = [24];
    let mut output_values = [0i64];

    assert_ok!(fmu.setInt64(&input_vr, &input_values));
    assert_ok!(fmu.getInt64(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_uint64() {
    let mut fmu = create_fmu();

    let input_vr = [25];
    let input_values = [18446744073709551615u64];

    let output_vr = [26];
    let mut output_values = [0u64];

    assert_ok!(fmu.setUInt64(&input_vr, &input_values));
    assert_ok!(fmu.getUInt64(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_boolean() {
    let mut fmu = create_fmu();

    let input_vr = [27];
    let input_values = [true];

    let output_vr = [28];
    let mut output_values = [false];

    assert_ok!(fmu.setBoolean(&input_vr, &input_values));
    assert_ok!(fmu.getBoolean(&output_vr, &mut output_values));
    assert_eq!(output_values, input_values);

    // Test with false value
    let input_values_false = [false];
    let mut output_values_false = [true];

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
    let input_values = ["Hello, FMI3!"];

    let output_vr = [30];
    let mut output_values = [String::new()];

    assert_ok!(fmu.setString(&input_vr, &input_values));
    assert_ok!(fmu.getString(&output_vr, &mut output_values));

    assert_eq!(output_values[0], input_values[0]);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_binary() {
    let mut fmu = create_fmu();

    let input_vr = [31];
    let input_data = b"Hello, Binary World!";
    let input_sizes = [input_data.len()];

    let output_vr = [32];
    let output_data = vec![0u8; 100]; // Allocate enough space
    let mut output_sizes = [100usize]; // Set initial size to buffer capacity
    let mut output_ptrs = [output_data.as_ptr()]; // Use as_ptr() not as_mut_ptr()

    assert_ok!(fmu.setBinary(&input_vr, &input_sizes, &[input_data.as_ptr()]));
    assert_ok!(fmu.getBinary(&output_vr, &mut output_sizes, &mut output_ptrs));

    // The FMU should have updated the pointer to point to its internal buffer
    // We need to copy the data from the returned pointer
    let returned_data = unsafe { std::slice::from_raw_parts(output_ptrs[0], output_sizes[0]) };

    // Compare the actual data
    assert_eq!(output_sizes[0], input_sizes[0]);
    assert_eq!(returned_data, input_data);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_multiple_variables() {
    let mut fmu = create_fmu();

    // Test setting and getting multiple different variable types in one test

    // Float64
    let float64_input_vr = [7];
    let float64_input_values = [123.456];
    let float64_output_vr = [8];
    let mut float64_output_values = [0.0];

    // Int32
    let int32_input_vr = [19];
    let int32_input_values = [42];
    let int32_output_vr = [20];
    let mut int32_output_values = [0];

    // Boolean
    let bool_input_vr = [27];
    let bool_input_values = [true];
    let bool_output_vr = [28];
    let mut bool_output_values = [false];

    // Set all input values
    assert_ok!(fmu.setFloat64(&float64_input_vr, &float64_input_values));
    assert_ok!(fmu.setInt32(&int32_input_vr, &int32_input_values));
    assert_ok!(fmu.setBoolean(&bool_input_vr, &bool_input_values));

    // Get all output values
    assert_ok!(fmu.getFloat64(&float64_output_vr, &mut float64_output_values));
    assert_ok!(fmu.getInt32(&int32_output_vr, &mut int32_output_values));
    assert_ok!(fmu.getBoolean(&bool_output_vr, &mut bool_output_values));

    // Verify all values
    assert_eq!(float64_output_values, float64_input_values);
    assert_eq!(int32_output_values, int32_input_values);
    assert_eq!(bool_output_values, bool_input_values);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}

#[test]
fn test_edge_cases() {
    let mut fmu = create_fmu();

    // Test extreme values for different types

    // Float32 edge cases
    let float32_input_vr = [1];
    let float32_output_vr = [2];

    // Test positive infinity
    let pos_inf = [f32::INFINITY];
    let mut output = [0.0f32];
    assert_ok!(fmu.setFloat32(&float32_input_vr, &pos_inf));
    assert_ok!(fmu.getFloat32(&float32_output_vr, &mut output));
    assert!(output[0].is_infinite() && output[0].is_sign_positive());

    // Test negative infinity
    let neg_inf = [f32::NEG_INFINITY];
    assert_ok!(fmu.setFloat32(&float32_input_vr, &neg_inf));
    assert_ok!(fmu.getFloat32(&float32_output_vr, &mut output));
    assert!(output[0].is_infinite() && output[0].is_sign_negative());

    // Test NaN
    let nan = [f32::NAN];
    assert_ok!(fmu.setFloat32(&float32_input_vr, &nan));
    assert_ok!(fmu.getFloat32(&float32_output_vr, &mut output));
    assert!(output[0].is_nan());

    // Test minimum and maximum integer values
    let int32_input_vr = [19];
    let int32_output_vr = [20];

    let max_int32 = [i32::MAX];
    let mut int32_output = [0i32];
    assert_ok!(fmu.setInt32(&int32_input_vr, &max_int32));
    assert_ok!(fmu.getInt32(&int32_output_vr, &mut int32_output));
    assert_eq!(int32_output, max_int32);

    let min_int32 = [i32::MIN];
    assert_ok!(fmu.setInt32(&int32_input_vr, &min_int32));
    assert_ok!(fmu.getInt32(&int32_output_vr, &mut int32_output));
    assert_eq!(int32_output, min_int32);

    assert_ok!(fmu.terminate());
    fmu.freeInstance();
}
