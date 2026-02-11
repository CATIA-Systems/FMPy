#![allow(non_camel_case_types, non_snake_case)]

use fmi::fmi2::types::*;
use fmi::{fmi2::*};
use std::{
    path::{Path, PathBuf},
};
use url::Url;

macro_rules! assert_ok {
    ($expression:expr) => {
        assert_eq!($expression, fmi2OK);
    };
}



#[test]
fn test_fmi2_container() {

    let resource_path = PathBuf::from(r"E:\WS\FMPy\tests\work\resources");
    let dll_path = Path::new(r"E:\WS\FMPy\tests\work\binaries\win64\container_fmu.dll");

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
        "",
        Some(&resource_url),
        false,
        true,
    ));

    // let Real_continuous_input_vr = [3];
    // let mut Real_continuous_input_values = [1.1];

    // let Real_continuous_output_vr = [4];
    // let mut Real_continuous_output_values = [0.0];

    // // set an input value
    // assert_ok!(fmu.setReal(&Real_continuous_input_vr, &Real_continuous_input_values));

    assert_ok!(fmu.setupExperiment(None, 0.0, None));
    assert_ok!(fmu.enterInitializationMode());
    assert_ok!(fmu.exitInitializationMode());

    // // check if the value has been forwarded after exiting intialization mode
    // assert_ok!(fmu.getReal(
    //     &Real_continuous_output_vr,
    //     &mut Real_continuous_output_values
    // ));
    // assert_eq!(Real_continuous_output_values, Real_continuous_input_values);

    // // set a different input value
    // Real_continuous_input_values[0] = 1.2;
    // assert_ok!(fmu.setReal(&Real_continuous_input_vr, &Real_continuous_input_values));

    // assert_ok!(fmu.doStep(0.0, 0.5, fmi2True));

    // // check if the value has been forwarded after the doStep
    // assert_ok!(fmu.getReal(
    //     &Real_continuous_output_vr,
    //     &mut Real_continuous_output_values
    // ));
    // assert_eq!(Real_continuous_output_values, Real_continuous_input_values);

    assert_ok!(fmu.terminate());

    fmu.freeInstance();
}
