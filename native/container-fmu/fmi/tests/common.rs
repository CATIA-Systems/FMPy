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
pub fn ensure_feedthrough_fmus() -> Result<(), Box<dyn std::error::Error>> {
    let mut setup_done = SETUP_DONE.get_or_init(|| Mutex::new(false)).lock().unwrap();
    
    if *setup_done {
        return Ok(());
    }

    let workspace_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .to_path_buf();

    let fmi2_feedthrough = workspace_root
        .join("fmi")
        .join("tests")
        .join("resources")
        .join("fmi2")
        .join("Feedthrough");

    let fmi3_feedthrough = workspace_root
        .join("fmi")
        .join("tests")
        .join("resources")
        .join("fmi3")
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
