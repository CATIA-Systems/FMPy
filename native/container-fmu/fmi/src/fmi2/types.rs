#![allow(non_camel_case_types, non_snake_case, non_upper_case_globals)]

use crate::types::*;
use std::os::raw::{c_char, c_void};

pub type fmi2Real = f64;
pub type fmi2Integer = i32;
pub type fmi2Boolean = i32;
pub type fmi2Char = c_char;
pub type fmi2String = *const c_char;
pub type fmi2Byte = u8;
pub type fmi2ValueReference = fmiValueReference;
pub type fmi2FMUstate = *mut c_void;
pub type fmi2Component = *mut c_void;
pub type fmi2ComponentEnvironment = *mut c_void;

pub const fmi2True: fmi2Boolean = 1;
pub const fmi2False: fmi2Boolean = 0;

pub type fmi2Status = fmiStatus;

pub use crate::types::fmiStatus::fmiError as fmi2Error;
pub use crate::types::fmiStatus::fmiFatal as fmi2Fatal;
pub use crate::types::fmiStatus::fmiOK as fmi2OK;
pub use crate::types::fmiStatus::fmiPending as fmi2Pending;
pub use crate::types::fmiStatus::fmiWarning as fmi2Warning;

#[repr(i32)]
#[derive(Debug, PartialEq, Clone, Copy)]
pub enum fmi2Type {
    fmi2ModelExchange = 0,
    fmi2CoSimulation = 1,
}

#[repr(i32)]
#[derive(Debug, PartialEq, Clone, Copy)]
pub enum fmi2DependencyKind {
    fmi2Independent = 0,
    fmi2Constant = 1,
    fmi2Fixed = 2,
    fmi2Tunable = 3,
    fmi2Discrete = 4,
    fmi2Dependent = 5,
}

#[repr(i32)]
#[derive(Debug, PartialEq, Clone, Copy)]
pub enum fmi2VariableType {
    Real,
    Integer,
    Boolean,
    String,
}

pub type fmi2CallbackLogger = unsafe extern "C" fn(
    componentEnvironment: fmi2ComponentEnvironment,
    instanceName: fmi2String,
    status: fmi2Status,
    category: fmi2String,
    message: fmi2String,
);

pub type fmi2CallbackAllocateMemory = unsafe extern "C" fn(nobj: usize, size: usize) -> *mut c_void;

pub type fmi2CallbackFreeMemory = unsafe extern "C" fn(obj: *mut c_void);

pub type fmi2StepFinished =
    unsafe extern "C" fn(componentEnvironment: fmi2ComponentEnvironment, status: fmi2Status);

#[repr(C)]
pub struct fmi2CallbackFunctions {
    pub logger: fmi2CallbackLogger,
    pub allocateMemory: fmi2CallbackAllocateMemory,
    pub freeMemory: fmi2CallbackFreeMemory,
    pub stepFinished: fmi2StepFinished,
    pub componentEnvironment: fmi2ComponentEnvironment,
}

pub type fmi2GetVersionTYPE = unsafe extern "C" fn() -> fmi2String;

pub type fmi2GetTypesPlatformTYPE = unsafe extern "C" fn() -> fmi2String;

pub type fmi2SetDebugLoggingTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    loggingOn: fmi2Boolean,
    nCategories: usize,
    categories: *const fmi2String,
) -> fmi2Status;

pub type fmi2InstantiateTYPE = unsafe extern "C" fn(
    instanceName: fmi2String,
    fmuType: fmi2Type,
    fmuGUID: fmi2String,
    fmuResourceLocation: fmi2String,
    functions: *const fmi2CallbackFunctions,
    visible: fmi2Boolean,
    loggingOn: fmi2Boolean,
) -> fmi2Component;

pub type fmi2FreeInstanceTYPE = unsafe extern "C" fn(c: fmi2Component);

pub type fmi2SetupExperimentTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    toleranceDefined: fmi2Boolean,
    tolerance: fmi2Real,
    startTime: fmi2Real,
    stopTimeDefined: fmi2Boolean,
    stopTime: fmi2Real,
) -> fmi2Status;

pub type fmi2EnterInitializationModeTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2ExitInitializationModeTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2TerminateTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2ResetTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2GetRealTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Real,
) -> fmi2Status;

pub type fmi2GetIntegerTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Integer,
) -> fmi2Status;

pub type fmi2GetBooleanTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2Boolean,
) -> fmi2Status;

pub type fmi2GetStringTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *mut fmi2String,
) -> fmi2Status;

pub type fmi2SetRealTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Real,
) -> fmi2Status;

pub type fmi2SetIntegerTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Integer,
) -> fmi2Status;

pub type fmi2SetBooleanTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2Boolean,
) -> fmi2Status;

pub type fmi2SetStringTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    value: *const fmi2String,
) -> fmi2Status;

pub type fmi2GetFMUstateTYPE =
    unsafe extern "C" fn(c: fmi2Component, FMUstate: *mut fmi2FMUstate) -> fmi2Status;

pub type fmi2SetFMUstateTYPE =
    unsafe extern "C" fn(c: fmi2Component, FMUstate: fmi2FMUstate) -> fmi2Status;

pub type fmi2FreeFMUstateTYPE =
    unsafe extern "C" fn(c: fmi2Component, FMUstate: *mut fmi2FMUstate) -> fmi2Status;

pub type fmi2SerializedFMUstateSizeTYPE =
    unsafe extern "C" fn(c: fmi2Component, FMUstate: fmi2FMUstate, size: *mut usize) -> fmi2Status;

pub type fmi2SerializeFMUstateTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    FMUstate: fmi2FMUstate,
    serializedState: *mut fmi2Byte,
    size: usize,
) -> fmi2Status;

pub type fmi2DeSerializeFMUstateTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    serializedState: *const fmi2Byte,
    size: usize,
    FMUstate: *mut fmi2FMUstate,
) -> fmi2Status;

pub type fmi2GetDirectionalDerivativeTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vUnknown_ref: *const fmi2ValueReference,
    nUnknown: usize,
    vKnown_ref: *const fmi2ValueReference,
    nKnown: usize,
    dvKnown: *const fmi2Real,
    dvUnknown: *mut fmi2Real,
) -> fmi2Status;

pub type fmi2EnterEventModeTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2NewDiscreteStatesTYPE =
    unsafe extern "C" fn(c: fmi2Component, fmi2eventInfo: *mut fmi2EventInfo) -> fmi2Status;

pub type fmi2EnterContinuousTimeModeTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2CompletedIntegratorStepTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
    enterEventMode: *mut fmi2Boolean,
    terminateSimulation: *mut fmi2Boolean,
) -> fmi2Status;

pub type fmi2SetTimeTYPE = unsafe extern "C" fn(c: fmi2Component, time: fmi2Real) -> fmi2Status;

pub type fmi2SetContinuousStatesTYPE =
    unsafe extern "C" fn(c: fmi2Component, x: *const fmi2Real, nx: usize) -> fmi2Status;

pub type fmi2GetDerivativesTYPE =
    unsafe extern "C" fn(c: fmi2Component, derivatives: *mut fmi2Real, nx: usize) -> fmi2Status;

pub type fmi2GetEventIndicatorsTYPE =
    unsafe extern "C" fn(c: fmi2Component, eventIndicators: *mut fmi2Real, ni: usize) -> fmi2Status;

pub type fmi2GetContinuousStatesTYPE =
    unsafe extern "C" fn(c: fmi2Component, x: *mut fmi2Real, nx: usize) -> fmi2Status;

pub type fmi2GetNominalsOfContinuousStatesTYPE =
    unsafe extern "C" fn(c: fmi2Component, x_nominal: *mut fmi2Real, nx: usize) -> fmi2Status;

pub type fmi2SetRealInputDerivativesTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    order: *const fmi2Integer,
    value: *const fmi2Real,
) -> fmi2Status;

pub type fmi2GetRealOutputDerivativesTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    vr: *const fmi2ValueReference,
    nvr: usize,
    order: *const fmi2Integer,
    value: *mut fmi2Real,
) -> fmi2Status;

pub type fmi2DoStepTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    currentCommunicationPoint: fmi2Real,
    communicationStepSize: fmi2Real,
    noSetFMUStatePriorToCurrentPoint: fmi2Boolean,
) -> fmi2Status;

pub type fmi2CancelStepTYPE = unsafe extern "C" fn(c: fmi2Component) -> fmi2Status;

pub type fmi2GetStatusTYPE =
    unsafe extern "C" fn(c: fmi2Component, s: fmi2StatusKind, value: *mut fmi2Status) -> fmi2Status;

pub type fmi2GetRealStatusTYPE =
    unsafe extern "C" fn(c: fmi2Component, s: fmi2StatusKind, value: *mut fmi2Real) -> fmi2Status;

pub type fmi2GetIntegerStatusTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Integer,
) -> fmi2Status;

pub type fmi2GetBooleanStatusTYPE = unsafe extern "C" fn(
    c: fmi2Component,
    s: fmi2StatusKind,
    value: *mut fmi2Boolean,
) -> fmi2Status;

pub type fmi2GetStringStatusTYPE =
    unsafe extern "C" fn(c: fmi2Component, s: fmi2StatusKind, value: *mut fmi2String) -> fmi2Status;

#[repr(i32)]
#[derive(Debug, PartialEq, Clone, Copy)]
pub enum fmi2StatusKind {
    fmi2DoStepStatus = 0,
    fmi2PendingStatus = 1,
    fmi2LastSuccessfulTime = 2,
    fmi2Terminated = 3,
}

#[repr(C)]
#[derive(Debug)]
pub struct fmi2EventInfo {
    pub newDiscreteStatesNeeded: fmi2Boolean,
    pub terminateSimulation: fmi2Boolean,
    pub nominalsOfContinuousStatesChanged: fmi2Boolean,
    pub valuesOfContinuousStatesChanged: fmi2Boolean,
    pub nextEventTimeDefined: fmi2Boolean,
    pub nextEventTime: fmi2Real,
}
