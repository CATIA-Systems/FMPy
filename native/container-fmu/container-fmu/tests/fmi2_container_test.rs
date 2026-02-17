#![allow(non_camel_case_types, non_snake_case)]

mod common;

use common::create_fmi2_container;
use fmi::fmi2::types::*;

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi2OK);
    };
}

#[test]
fn test_fmi2_container() {

    let fmu = create_fmi2_container();

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
