#![allow(unused)]

use fmi::{SHARED_LIBRARY_EXTENSION, fmi2::{FMU2, PLATFORM, types::*}, fmi3::{FMU3, PLATFORM_TUPLE, types::fmi3Status}};
use rstest::*;
use std::{env, path::PathBuf, sync::Mutex};
use std::sync::OnceLock;
use std::fs;
use std::io::{Read, Write};
use sha2::{Sha256, Digest};

static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
static SETUP_DONE: OnceLock<Mutex<bool>> = OnceLock::new();

const REFERENCE_FMUS_URL: &str = "https://github.com/modelica/Reference-FMUs/releases/download/v0.0.39/Reference-FMUs-0.0.39.zip";
const EXPECTED_SHA256: &str = "6863d55e5818e1ca4e4614c4d4ba4047a921b4495f6336e7002874ed791f6c2a";

/// Setup fixture that ensures Feedthrough FMUs are available
fn ensure_feedthrough_fmus() -> Result<(), Box<dyn std::error::Error>> {
    let mut setup_done = SETUP_DONE.get_or_init(|| Mutex::new(false)).lock().unwrap();
    
    if *setup_done {
        return Ok(());
    }

    let workspace_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();

    let fmi2_feedthrough = workspace_root
        .join("container-fmu")
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("resources")
        .join("Feedthrough");

    let fmi3_feedthrough = workspace_root
        .join("container-fmu")
        .join("tests")
        .join("resources")
        .join("fmi3")
        .join("resources")
        .join("Feedthrough");

    // Check if both directories exist
    if fmi2_feedthrough.exists() && fmi3_feedthrough.exists() {
        println!("Feedthrough FMUs already exist, skipping download");
        *setup_done = true;
        return Ok(());
    }

    println!("Downloading Reference FMUs from {}", REFERENCE_FMUS_URL);

    // Download the zip file
    let response = reqwest::blocking::get(REFERENCE_FMUS_URL)?;
    let bytes = response.bytes()?;

    // Validate SHA256 checksum
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let hash = format!("{:x}", hasher.finalize());

    if hash != EXPECTED_SHA256 {
        return Err(format!(
            "SHA256 checksum mismatch. Expected: {}, Got: {}",
            EXPECTED_SHA256, hash
        ).into());
    }

    println!("SHA256 checksum validated successfully");

    // Create a temporary file for the zip
    let temp_dir = tempfile::tempdir()?;
    let zip_path = temp_dir.path().join("reference-fmus.zip");
    let mut file = fs::File::create(&zip_path)?;
    file.write_all(&bytes)?;

    println!("Extracting FMUs...");

    // Extract the zip file
    let file = fs::File::open(&zip_path)?;
    let mut archive = zip::ZipArchive::new(file)?;

    // Extract FMI2 Feedthrough.fmu
    let fmi2_fmu_path = "2.0/Feedthrough.fmu";
    
    if let Ok(mut fmu_file) = archive.by_name(fmi2_fmu_path) {
        let mut fmu_bytes = Vec::new();
        fmu_file.read_to_end(&mut fmu_bytes)?;
        
        // Extract the FMU (which is also a zip file)
        let fmu_cursor = std::io::Cursor::new(fmu_bytes);
        let mut fmu_archive = zip::ZipArchive::new(fmu_cursor)?;
        
        fs::create_dir_all(&fmi2_feedthrough)?;
        
        for i in 0..fmu_archive.len() {
            let mut file = fmu_archive.by_index(i)?;
            let outpath = fmi2_feedthrough.join(file.name());
            
            if file.is_dir() {
                fs::create_dir_all(&outpath)?;
            } else {
                if let Some(parent) = outpath.parent() {
                    fs::create_dir_all(parent)?;
                }
                let mut outfile = fs::File::create(&outpath)?;
                std::io::copy(&mut file, &mut outfile)?;
            }
        }
        println!("Extracted FMI2 Feedthrough to {:?}", fmi2_feedthrough);
    } else {
        return Err(format!("Failed to extract {fmi2_fmu_path}.").into());
    }

    // Extract FMI3 Feedthrough.fmu
    let fmi3_fmu_path = "3.0/Feedthrough.fmu";

    if let Ok(mut fmu_file) = archive.by_name(fmi3_fmu_path) {
        let mut fmu_bytes = Vec::new();
        fmu_file.read_to_end(&mut fmu_bytes)?;
        
        // Extract the FMU (which is also a zip file)
        let fmu_cursor = std::io::Cursor::new(fmu_bytes);
        let mut fmu_archive = zip::ZipArchive::new(fmu_cursor)?;
        
        fs::create_dir_all(&fmi3_feedthrough)?;
        
        for i in 0..fmu_archive.len() {
            let mut file = fmu_archive.by_index(i)?;
            let outpath = fmi3_feedthrough.join(file.name());
            
            if file.is_dir() {
                fs::create_dir_all(&outpath)?;
            } else {
                if let Some(parent) = outpath.parent() {
                    fs::create_dir_all(parent)?;
                }
                let mut outfile = fs::File::create(&outpath)?;
                std::io::copy(&mut file, &mut outfile)?;
            }
        }
        println!("Extracted FMI3 Feedthrough to {:?}", fmi3_feedthrough);
    } else {
        return Err(format!("Failed to extract {fmi3_fmu_path}.").into());
    }

    *setup_done = true;
    Ok(())
}

#[fixture]
pub fn create_fmi2_container() -> FMU2 {

    let _guard = LOCK.get_or_init(|| Mutex::new(())).lock().unwrap();

    // Ensure Feedthrough FMUs are available
    ensure_feedthrough_fmus().expect("Failed to setup Feedthrough FMUs");

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
        let build_type = if cfg!(debug_assertions) { "debug" } else { "release" };
        let shared_library_artifact = workspace_root.join("target").join(build_type).join(shared_library_name);
        
        dbg!(&shared_library_artifact);
        dbg!(&platform_binary);
        
        std::fs::copy(shared_library_artifact, platform_binary).unwrap();
    }

    let log_message = move |status: &fmi2Status, category: &str, message: &str| {
        println!("[{status:?}] [{category}] {message}")
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

pub fn create_fmi3_container() -> FMU3 {

    let _guard = LOCK.get_or_init(|| Mutex::new(())).lock().unwrap();

    // Ensure Feedthrough FMUs are available
    ensure_feedthrough_fmus().expect("Failed to setup Feedthrough FMUs");

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
        let build_type = if cfg!(debug_assertions) { "debug" } else { "release" };
        let shared_library_artifact = workspace_root.join("target").join(build_type).join(shared_library_name);
        std::fs::copy(shared_library_artifact, platform_binary).unwrap();
    }

    let log_message = move |status: &fmi3Status, category: &str, message: &str| {
        println!(" [{status:?}] [{category}] {message}")
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