#ifndef fmi3Functions_h
#define fmi3Functions_h

/*
This header file must be utilized when compiling a FMU.
It defines all functions of the
     FMI 3.0-wg003.3 Model Exchange and Co-Simulation Interface.

In order to have unique function names even if several FMUs
are compiled together (e.g. for embedded systems), every "real" function name
is constructed by prepending the function name by "FMI3_FUNCTION_PREFIX".
Therefore, the typical usage is:

  #define FMI3_FUNCTION_PREFIX MyModel_
  #include "fmi3Functions.h"

As a result, a function that is defined as "fmi3GetDerivatives" in this header file,
is actually getting the name "MyModel_fmi3GetDerivatives".

This only holds if the FMU is shipped in C source code, or is compiled in a
static link library. For FMUs compiled in a DLL/sharedObject, the "actual" function
names are used and "FMI3_FUNCTION_PREFIX" must not be defined.

Copyright (C) 2008-2011 MODELISAR consortium,
              2012-2019 Modelica Association Project "FMI"
              All rights reserved.

This file is licensed by the copyright holders under the 2-Clause BSD License
(https://opensource.org/licenses/BSD-2-Clause):

----------------------------------------------------------------------------
Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

- Redistributions of source code must retain the above copyright notice,
 this list of conditions and the following disclaimer.

- Redistributions in binary form must reproduce the above copyright notice,
 this list of conditions and the following disclaimer in the documentation
 and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
----------------------------------------------------------------------------
*/

#ifdef __cplusplus
extern "C" {
#endif

#include "fmi3PlatformTypes.h"
#include "fmi3FunctionTypes.h"
#include <stdlib.h>

/*
Export FMI3 API functions on Windows and under GCC.
If custom linking is desired then the FMI3_Export must be
defined before including this file. For instance,
it may be set to __declspec(dllimport).
*/
#if !defined(FMI3_Export)
  #if !defined(FMI3_FUNCTION_PREFIX)
    #if defined _WIN32 || defined __CYGWIN__
     /* Note: both gcc & MSVC on Windows support this syntax. */
        #define FMI3_Export __declspec(dllexport)
    #else
      #if __GNUC__ >= 4
        #define FMI3_Export __attribute__ ((visibility ("default")))
      #else
        #define FMI3_Export
      #endif
    #endif
  #else
    #define FMI3_Export
  #endif
#endif

/*
Macros to construct the real function name (prepend function name by FMI3_FUNCTION_PREFIX)
*/
#if defined(FMI3_FUNCTION_PREFIX)
  #define fmi3Paste(a,b)     a ## b
  #define fmi3PasteB(a,b)    fmi3Paste(a,b)
  #define fmi3FullName(name) fmi3PasteB(FMI3_FUNCTION_PREFIX, name)
#else
  #define fmi3FullName(name) name
#endif

/***************************************************
Common Functions
****************************************************/
#define fmi3GetVersion               fmi3FullName(fmi3GetVersion)
#define fmi3SetDebugLogging          fmi3FullName(fmi3SetDebugLogging)
#define fmi3Instantiate              fmi3FullName(fmi3Instantiate)
#define fmi3FreeInstance             fmi3FullName(fmi3FreeInstance)
#define fmi3SetupExperiment          fmi3FullName(fmi3SetupExperiment)
#define fmi3EnterInitializationMode  fmi3FullName(fmi3EnterInitializationMode)
#define fmi3ExitInitializationMode   fmi3FullName(fmi3ExitInitializationMode)
#define fmi3Terminate                fmi3FullName(fmi3Terminate)
#define fmi3Reset                    fmi3FullName(fmi3Reset)
#define fmi3GetFloat32               fmi3FullName(fmi3GetFloat32)
#define fmi3GetFloat64               fmi3FullName(fmi3GetFloat64)
#define fmi3GetInt8                  fmi3FullName(fmi3GetInt8)
#define fmi3GetUInt8                 fmi3FullName(fmi3GetUInt8)
#define fmi3GetInt16                 fmi3FullName(fmi3GetInt16)
#define fmi3GetUInt16                fmi3FullName(fmi3GetUInt16)
#define fmi3GetInt32                 fmi3FullName(fmi3GetInt32)
#define fmi3GetUInt32                fmi3FullName(fmi3GetUInt32)
#define fmi3GetInt64                 fmi3FullName(fmi3GetInt64)
#define fmi3GetUInt64                fmi3FullName(fmi3GetUInt64)
#define fmi3GetBoolean               fmi3FullName(fmi3GetBoolean)
#define fmi3GetString                fmi3FullName(fmi3GetString)
#define fmi3GetBinary                fmi3FullName(fmi3GetBinary)
#define fmi3SetFloat32               fmi3FullName(fmi3SetFloat32)
#define fmi3SetFloat64               fmi3FullName(fmi3SetFloat64)
#define fmi3SetInt8                  fmi3FullName(fmi3SetInt8)
#define fmi3SetUInt8                 fmi3FullName(fmi3SetUInt8)
#define fmi3SetInt16                 fmi3FullName(fmi3SetInt16)
#define fmi3SetUInt16                fmi3FullName(fmi3SetUInt16)
#define fmi3SetInt32                 fmi3FullName(fmi3SetInt32)
#define fmi3SetUInt32                fmi3FullName(fmi3SetUInt32)
#define fmi3SetInt64                 fmi3FullName(fmi3SetInt64)
#define fmi3SetUInt64                fmi3FullName(fmi3SetUInt64)
#define fmi3SetBoolean               fmi3FullName(fmi3SetBoolean)
#define fmi3SetString                fmi3FullName(fmi3SetString)
#define fmi3SetBinary                fmi3FullName(fmi3SetBinary)
#define fmi3GetNumberOfVariableDependencies fmi3FullName(fmi3GetNumberOfVariableDependencies)
#define fmi3GetVariableDependencies  fmi3FullName(fmi3GetVariableDependencies)
#define fmi3GetFMUState              fmi3FullName(fmi3GetFMUState)
#define fmi3SetFMUState              fmi3FullName(fmi3SetFMUState)
#define fmi3FreeFMUState             fmi3FullName(fmi3FreeFMUState)
#define fmi3SerializedFMUStateSize   fmi3FullName(fmi3SerializedFMUStateSize)
#define fmi3SerializeFMUState        fmi3FullName(fmi3SerializeFMUState)
#define fmi3DeSerializeFMUState      fmi3FullName(fmi3DeSerializeFMUState)
#define fmi3GetDirectionalDerivative fmi3FullName(fmi3GetDirectionalDerivative)

/***************************************************
Functions for FMI3 for Model Exchange
****************************************************/

#define fmi3EnterEventMode                fmi3FullName(fmi3EnterEventMode)
#define fmi3NewDiscreteStates             fmi3FullName(fmi3NewDiscreteStates)
#define fmi3EnterContinuousTimeMode       fmi3FullName(fmi3EnterContinuousTimeMode)
#define fmi3CompletedIntegratorStep       fmi3FullName(fmi3CompletedIntegratorStep)
#define fmi3SetTime                       fmi3FullName(fmi3SetTime)
#define fmi3SetContinuousStates           fmi3FullName(fmi3SetContinuousStates)
#define fmi3GetDerivatives                fmi3FullName(fmi3GetDerivatives)
#define fmi3GetEventIndicators            fmi3FullName(fmi3GetEventIndicators)
#define fmi3GetContinuousStates           fmi3FullName(fmi3GetContinuousStates)
#define fmi3GetNominalsOfContinuousStates fmi3FullName(fmi3GetNominalsOfContinuousStates)
#define fmi3GetNumberOfEventIndicators    fmi3FullName(fmi3GetNumberOfEventIndicators)
#define fmi3GetNumberOfContinuousStates   fmi3FullName(fmi3GetNumberOfContinuousStates)

/***************************************************
Functions for FMI3 for Co-Simulation
****************************************************/

#define fmi3SetInputDerivatives          fmi3FullName(fmi3SetInputDerivatives)
#define fmi3GetOutputDerivatives         fmi3FullName(fmi3GetOutputDerivatives)
#define fmi3DoStep                       fmi3FullName(fmi3DoStep)
#define fmi3CancelStep                   fmi3FullName(fmi3CancelStep)
#define fmi3GetDoStepPendingStatus       fmi3FullName(fmi3GetDoStepPendingStatus)
#define fmi3GetDoStepDiscardedStatus     fmi3FullName(fmi3GetDoStepDiscardedStatus)

/* Version number */
#define fmi3Version "3.0-wg003.3"

/***************************************************
Common Functions
****************************************************/

/* Inquire version numbers and set debug logging */
FMI3_Export fmi3GetVersionTYPE       fmi3GetVersion;
FMI3_Export fmi3SetDebugLoggingTYPE  fmi3SetDebugLogging;

/* Creation and destruction of FMU instances */
FMI3_Export fmi3InstantiateTYPE  fmi3Instantiate;
FMI3_Export fmi3FreeInstanceTYPE fmi3FreeInstance;

/* Enter and exit initialization mode, terminate and reset */
FMI3_Export fmi3SetupExperimentTYPE         fmi3SetupExperiment;
FMI3_Export fmi3EnterInitializationModeTYPE fmi3EnterInitializationMode;
FMI3_Export fmi3ExitInitializationModeTYPE  fmi3ExitInitializationMode;
FMI3_Export fmi3TerminateTYPE               fmi3Terminate;
FMI3_Export fmi3ResetTYPE                   fmi3Reset;

/* Getting and setting variables values */
FMI3_Export fmi3GetFloat32TYPE fmi3GetFloat32;
FMI3_Export fmi3GetFloat64TYPE fmi3GetFloat64;
FMI3_Export fmi3GetInt8TYPE    fmi3GetInt8;
FMI3_Export fmi3GetUInt8TYPE   fmi3GetUInt8;
FMI3_Export fmi3GetInt16TYPE   fmi3GetInt16;
FMI3_Export fmi3GetUInt16TYPE  fmi3GetUInt16;
FMI3_Export fmi3GetInt32TYPE   fmi3GetInt32;
FMI3_Export fmi3GetUInt32TYPE  fmi3GetUInt32;
FMI3_Export fmi3GetInt64TYPE   fmi3GetInt64;
FMI3_Export fmi3GetUInt64TYPE  fmi3GetUInt64;
FMI3_Export fmi3GetBooleanTYPE fmi3GetBoolean;
FMI3_Export fmi3GetStringTYPE  fmi3GetString;
FMI3_Export fmi3GetBinaryTYPE  fmi3GetBinary;
FMI3_Export fmi3SetFloat32TYPE fmi3SetFloat32;
FMI3_Export fmi3SetFloat64TYPE fmi3SetFloat64;
FMI3_Export fmi3SetInt8TYPE    fmi3SetInt8;
FMI3_Export fmi3SetUInt8TYPE   fmi3SetUInt8;
FMI3_Export fmi3SetInt16TYPE   fmi3SetInt16;
FMI3_Export fmi3SetUInt16TYPE  fmi3SetUInt16;
FMI3_Export fmi3SetInt32TYPE   fmi3SetInt32;
FMI3_Export fmi3SetUInt32TYPE  fmi3SetUInt32;
FMI3_Export fmi3SetInt64TYPE   fmi3SetInt64;
FMI3_Export fmi3SetUInt64TYPE  fmi3SetUInt64;
FMI3_Export fmi3SetBooleanTYPE fmi3SetBoolean;
FMI3_Export fmi3SetStringTYPE  fmi3SetString;
FMI3_Export fmi3SetBinaryTYPE  fmi3SetBinary;
FMI3_Export fmi3SetStringTYPE  fmi3SetString;
FMI3_Export fmi3SetBinaryTYPE  fmi3SetBinary;

/* Getting Variable Dependency Information */
FMI3_Export fmi3GetNumberOfVariableDependenciesTYPE fmi3GetNumberOfVariableDependencies;
FMI3_Export fmi3GetVariableDependenciesTYPE         fmi3GetVariableDependencies;

/* Getting and setting the internal FMU state */
FMI3_Export fmi3GetFMUStateTYPE            fmi3GetFMUState;
FMI3_Export fmi3SetFMUStateTYPE            fmi3SetFMUState;
FMI3_Export fmi3FreeFMUStateTYPE           fmi3FreeFMUState;
FMI3_Export fmi3SerializedFMUStateSizeTYPE fmi3SerializedFMUStateSize;
FMI3_Export fmi3SerializeFMUStateTYPE      fmi3SerializeFMUState;
FMI3_Export fmi3DeSerializeFMUStateTYPE    fmi3DeSerializeFMUState;

/* Getting partial derivatives */
FMI3_Export fmi3GetDirectionalDerivativeTYPE fmi3GetDirectionalDerivative;

/***************************************************
Functions for FMI3 for Model Exchange
****************************************************/

/* Enter and exit the different modes */
FMI3_Export fmi3EnterEventModeTYPE               fmi3EnterEventMode;
FMI3_Export fmi3NewDiscreteStatesTYPE            fmi3NewDiscreteStates;
FMI3_Export fmi3EnterContinuousTimeModeTYPE      fmi3EnterContinuousTimeMode;
FMI3_Export fmi3CompletedIntegratorStepTYPE      fmi3CompletedIntegratorStep;

/* Providing independent variables and re-initialization of caching */
FMI3_Export fmi3SetTimeTYPE             fmi3SetTime;
FMI3_Export fmi3SetContinuousStatesTYPE fmi3SetContinuousStates;

/* Evaluation of the model equations */
FMI3_Export fmi3GetDerivativesTYPE                fmi3GetDerivatives;
FMI3_Export fmi3GetEventIndicatorsTYPE            fmi3GetEventIndicators;
FMI3_Export fmi3GetContinuousStatesTYPE           fmi3GetContinuousStates;
FMI3_Export fmi3GetNominalsOfContinuousStatesTYPE fmi3GetNominalsOfContinuousStates;
FMI3_Export fmi3GetNumberOfEventIndicatorsTYPE    fmi3GetNumberOfEventIndicators;
FMI3_Export fmi3GetNumberOfContinuousStatesTYPE   fmi3GetNumberOfContinuousStates;

/***************************************************
Functions for FMI3 for Co-Simulation
****************************************************/

/* Simulating the slave */
FMI3_Export fmi3SetInputDerivativesTYPE  fmi3SetInputDerivatives;
FMI3_Export fmi3GetOutputDerivativesTYPE fmi3GetOutputDerivatives;

FMI3_Export fmi3DoStepTYPE     fmi3DoStep;
FMI3_Export fmi3CancelStepTYPE fmi3CancelStep;

/* Inquire slave status */
FMI3_Export fmi3GetDoStepPendingStatusTYPE   fmi3GetDoStepPendingStatus;
FMI3_Export fmi3GetDoStepDiscardedStatusTYPE fmi3GetDoStepDiscardedStatus;

#ifdef __cplusplus
}  /* end of extern "C" { */
#endif

#endif /* fmi3Functions_h */
