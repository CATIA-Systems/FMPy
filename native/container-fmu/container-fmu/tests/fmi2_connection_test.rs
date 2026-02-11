#![allow(non_camel_case_types, non_snake_case)]

mod common;

use rstest::*;
use fmi::fmi2::types::*;
use fmi::fmi2::FMU2;
use common::fmu;

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi2OK);
    };
}

#[rstest]
fn test_fmi2_real_continuous_connections(fmu: FMU2) {

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
}

#[rstest]
fn test_fmi2_real_discrete_connections(fmu: FMU2) {

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
}

#[rstest]
fn test_fmi2_integer_connections(fmu: FMU2) {

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
}

#[rstest]
fn test_fmi2_boolean_connections(fmu: FMU2) {

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
}

#[rstest]
fn test_fmi2_string_connections(fmu: FMU2) {

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
}

#[rstest]
fn test_fmi2_enumeration_connections(fmu: FMU2) {

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
}
