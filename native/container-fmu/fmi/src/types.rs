#![allow(non_camel_case_types, non_snake_case, non_upper_case_globals)]

use std::ffi::{c_char, c_void};

#[repr(i32)]
#[derive(Debug, PartialEq, PartialOrd, Clone, Eq, Ord, Copy)]
pub enum fmiStatus {
    fmiOK = 0,
    fmiWarning = 1,
    fmiDiscard = 2,
    fmiError = 3,
    fmiFatal = 4,
    fmiPending = 5,
}

impl TryFrom<i32> for fmiStatus {
    type Error = ();

    fn try_from(value: i32) -> Result<Self, Self::Error> {
        match value {
            0 => Ok(fmiStatus::fmiOK),
            1 => Ok(fmiStatus::fmiWarning),
            2 => Ok(fmiStatus::fmiDiscard),
            3 => Ok(fmiStatus::fmiError),
            4 => Ok(fmiStatus::fmiFatal),
            5 => Ok(fmiStatus::fmiPending),
            _ => Err(()),
        }
    }
}

pub type fmiFloat32 = f32;
pub type fmiFloat64 = f64;
pub type fmiInt8 = i8;
pub type fmiUInt8 = u8;
pub type fmiInt16 = i16;
pub type fmiUInt16 = u16;
pub type fmiInt32 = i32;
pub type fmiUInt32 = u32;
pub type fmiInt64 = i64;
pub type fmiUInt64 = u64;
pub type fmiBoolean = bool;
pub type fmiChar = c_char;
pub type fmiString = *const c_char;
pub type fmiByte = u8;
pub type fmiBinary = *const fmiByte;
pub type fmiClock = u32;
pub type fmiValueReference = u32;
pub type fmiFMUState = *mut c_void;
pub type fmiInstance = *mut c_void;
pub type fmiInstanceEnvironment = *mut c_void;

pub type LogFMICallCallback = dyn Fn(&fmiStatus, &str) + Send + Sync;
pub type LogMessageCallback = dyn Fn(&fmiStatus, &str, &str) + Send + Sync;
