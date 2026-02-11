#![allow(unused)]

use fmi::{SHARED_LIBRARY_EXTENSION, fmi2::{FMU2, PLATFORM, types::*}, fmi3::{FMU3, PLATFORM_TUPLE, types::fmi3Status}};
use rstest::*;
use std::{env, path::PathBuf};

#[fixture]
pub fn create_fmi2_container() -> FMU2<'static> {

    let workspace_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();

    let unzipdir = workspace_root
        .join("container-fmu")
        .join("tests")
        .join("resources")
        .join("fmi2");

    let platform_binary = unzipdir
        .join("binaries")
        .join(PLATFORM)
        .join(format!("container_fmu{SHARED_LIBRARY_EXTENSION}"));

    if !platform_binary.is_file() {
        let shared_library_name = format!("{}container_fmu{}", if cfg!(windows) { "" } else { "lib" }, SHARED_LIBRARY_EXTENSION);
        let shared_library_artifact = workspace_root.join("target").join("debug").join(shared_library_name);
        std::fs::copy(shared_library_artifact, platform_binary).unwrap();
    }

    let log_message = move |_status: &fmi2Status, _category: &str, _message: &str| {
        // println!("[{_status:?}] [{_category}] {_message}")
    };

    let log_fmi_call = move |_status: &fmi2Status, _message: &str| {
        // println!("[{_status:?}] {_message}")
    };

    FMU2::new(
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
    .unwrap()
}

pub fn create_fmi3_container() -> FMU3<'static> {

    let workspace_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();

    let unzipdir = workspace_root
        .join("container-fmu")
        .join("tests")
        .join("resources")
        .join("fmi3");

    let platform_binary = unzipdir
        .join("binaries")
        .join(PLATFORM_TUPLE)
        .join(format!("container_fmu{SHARED_LIBRARY_EXTENSION}"));

    if !platform_binary.is_file() {
        let shared_library_name = format!("{}container_fmu{}", if cfg!(windows) { "" } else { "lib" }, SHARED_LIBRARY_EXTENSION);
        let shared_library_artifact = workspace_root.join("target").join("debug").join(shared_library_name);
        std::fs::copy(shared_library_artifact, platform_binary).unwrap();
    }

    let log_message = move |status: &fmi3Status, category: &str, message: &str| {
        // println!(" [{status:?}] [{category}] {message}")
    };

    let log_fmi_call = move |status: &fmi3Status, message: &str| {   
        // println!(">[{status:?}] {message}");
    };

    FMU3::instantiateCoSimulation(
        &unzipdir,
        "container_fmu",
        "container",
        "{088cfe7e-cb81-4ca1-a83d-e7a5c3ff47fd}",
        false,
        true,
        false,
        false,
        &[],
        Some(Box::new(log_fmi_call)),
        Some(Box::new(log_message)),
    )
    .unwrap()
}