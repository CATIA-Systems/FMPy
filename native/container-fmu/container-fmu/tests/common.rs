use fmi::fmi2::{FMU2, types::*};
use rstest::*;
use std::{env, path::PathBuf};

#[fixture]
pub fn fmu() -> FMU2<'static> {
    let workspace_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();

    let unzipdir = workspace_root
        .join("container-fmu")
        .join("tests")
        .join("resources")
        .join("fmi2");

    // Setup logging callbacks
    let log_message = move |_status: &fmi2Status, _category: &str, _message: &str| {
        // println!("[{_status:?}] [{_category}] {_message}")
    };

    let log_fmi_call = move |_status: &fmi2Status, _message: &str| {
        // println!("[{_status:?}] {_message}")
    };

    // Create and initialize FMU
    let fmu = FMU2::new(
        &unzipdir,
        "container_fmu",
        "container",
        fmi2Type::fmi2CoSimulation,
        "f6cda2ea-6875-475c-b7dc-a43a33e69094",
        false,
        true,
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap();

    assert!(fmu.getVersion().starts_with("2."));

    fmu
}
