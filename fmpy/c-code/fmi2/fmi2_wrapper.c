/* Wrapper for FMI 2.0 C-code FMUs that re-exports the FMI API without prefix */

#include "fmi2Functions.h"


#if defined _WIN32 || defined __CYGWIN__
/* Note: both gcc & MSVC on Windows support this syntax. */
#define FMPY_EXPORT __declspec(dllexport)
#else
#if __GNUC__ >= 4
#define FMPY_EXPORT __attribute__ ((visibility ("default")))
#else
#define FMPY_EXPORT
#endif
#endif


/***************************************************
Common Functions for FMI 2.0
****************************************************/

/* Inquire version numbers of header files and setting logging status */

#undef fmi2GetTypesPlatform
FMPY_EXPORT const char* fmi2GetTypesPlatform() {
	return fmi2FullName(fmi2GetTypesPlatform)();
}

#undef fmi2GetVersion
FMPY_EXPORT const char* fmi2GetVersion() {
	return fmi2FullName(fmi2GetVersion)();
}

#undef fmi2SetDebugLogging
FMPY_EXPORT fmi2Status  fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {
	return fmi2FullName(fmi2SetDebugLogging)(c, loggingOn, nCategories, categories);
}

/* Creation and destruction of FMU instances and setting debug status */

#undef fmi2Instantiate
FMPY_EXPORT fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID, fmi2String fmuResourceLocation, const fmi2CallbackFunctions* functions, fmi2Boolean visible, fmi2Boolean loggingOn) {
	return fmi2FullName(fmi2Instantiate)(instanceName, fmuType, fmuGUID, fmuResourceLocation, functions, visible, loggingOn);
}

#undef fmi2FreeInstance
FMPY_EXPORT void fmi2FreeInstance(fmi2Component c) {
	fmi2FullName(fmi2FreeInstance)(c);
}

/* Enter and exit initialization mode, terminate and reset */
#undef fmi2SetupExperiment
FMPY_EXPORT fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) { 
	return fmi2FullName(fmi2SetupExperiment)(c, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime); 
}

#undef fmi2EnterInitializationMode
FMPY_EXPORT fmi2Status fmi2EnterInitializationMode(fmi2Component c) { 
	return fmi2FullName(fmi2EnterInitializationMode)(c);
}

#undef fmi2ExitInitializationMode
FMPY_EXPORT fmi2Status fmi2ExitInitializationMode(fmi2Component c) { 
	return fmi2FullName(fmi2ExitInitializationMode)(c);
}

#undef fmi2Terminate
FMPY_EXPORT fmi2Status fmi2Terminate(fmi2Component c) { 
	return fmi2FullName(fmi2Terminate)(c);
}

#undef fmi2Reset
FMPY_EXPORT fmi2Status fmi2Reset(fmi2Component c) { 
	return fmi2FullName(fmi2Reset)(c);
}


/* Getting and setting variable values */

#undef fmi2GetReal
FMPY_EXPORT fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) { 
	return fmi2FullName(fmi2GetReal)(c, vr, nvr, value);
}

#undef fmi2GetInteger
FMPY_EXPORT fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) { 
	return fmi2FullName(fmi2GetInteger)(c, vr, nvr, value);
}

#undef fmi2GetBoolean
FMPY_EXPORT fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) { 
	return fmi2FullName(fmi2GetBoolean)(c, vr, nvr, value);
}

#undef fmi2GetString
FMPY_EXPORT fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String value[]) {
	return fmi2FullName(fmi2GetString)(c, vr, nvr, value);
}

#undef fmi2SetReal
FMPY_EXPORT fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) { 
	return fmi2FullName(fmi2SetReal)(c, vr, nvr, value);
}

#undef fmi2SetInteger
FMPY_EXPORT fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
	return fmi2FullName(fmi2SetInteger)(c, vr, nvr, value);
}

#undef fmi2SetBoolean
FMPY_EXPORT fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) { 
	return fmi2FullName(fmi2SetBoolean)(c, vr, nvr, value);
}

#undef fmi2SetString
FMPY_EXPORT fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String value[]) {
	return fmi2FullName(fmi2SetString)(c, vr, nvr, value);
}

/* Getting and setting the internal FMU state */

#undef fmi2GetFMUstate
FMPY_EXPORT fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) { return fmi2FullName(fmi2GetFMUstate)(c, FMUstate); }

#undef fmi2SetFMUstate
FMPY_EXPORT fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) { return fmi2FullName(fmi2SetFMUstate)(c, FMUstate); }

#undef fmi2FreeFMUstate
FMPY_EXPORT fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) { return fmi2FullName(fmi2FreeFMUstate)(c, FMUstate); }

#undef fmi2SerializedFMUstateSize
FMPY_EXPORT fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t *size) { return fmi2FullName(fmi2SerializedFMUstateSize)(c, FMUstate, size); }

#undef fmi2SerializeFMUstate
FMPY_EXPORT fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate FMUstate, fmi2Byte serializedState[], size_t size) { return fmi2FullName(fmi2SerializeFMUstate)(c, FMUstate, serializedState, size); }

#undef fmi2DeSerializeFMUstate
FMPY_EXPORT fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) { return fmi2FullName(fmi2DeSerializeFMUstate)(c, serializedState, size, FMUstate); }

/* Getting partial derivatives */
#undef fmi2GetDirectionalDerivative
FMPY_EXPORT fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
	const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
	const fmi2ValueReference vKnown_ref[], size_t nKnown,
	const fmi2Real dvKnown[],
	fmi2Real dvUnknown[]) { 
	return fmi2FullName(fmi2GetDirectionalDerivative)(c, vUnknown_ref, nUnknown, vKnown_ref, nKnown, dvKnown, dvUnknown);
}

/***************************************************
Functions for FMI 2.0 for Model Exchange
****************************************************/

#ifdef MODEL_EXCHANGE

/* Enter and exit the different modes */

#undef fmi2EnterEventMode
FMPY_EXPORT fmi2Status fmi2EnterEventMode(fmi2Component c) { return fmi2FullName(fmi2EnterEventMode)(c); }

#undef fmi2NewDiscreteStates
FMPY_EXPORT fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) { return fmi2FullName(fmi2NewDiscreteStates)(c, eventInfo); }

#undef fmi2EnterContinuousTimeMode
FMPY_EXPORT fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) { return fmi2FullName(fmi2EnterContinuousTimeMode)(c); }

#undef fmi2CompletedIntegratorStep
FMPY_EXPORT fmi2Status fmi2CompletedIntegratorStep(fmi2Component c,
	fmi2Boolean noSetFMUStatePriorToCurrentPoint,
	fmi2Boolean* enterEventMode,
	fmi2Boolean* terminateSimulation) { 
	return fmi2FullName(fmi2CompletedIntegratorStep)(c, noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation);
}

/* Providing independent variables and re-initialization of caching */

#undef fmi2SetTime
FMPY_EXPORT fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) { return fmi2FullName(fmi2SetTime)(c, time); }

#undef fmi2SetContinuousStates
FMPY_EXPORT fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) { return fmi2FullName(fmi2SetContinuousStates)(c, x, nx); }

/* Evaluation of the model equations */

#undef fmi2GetDerivatives
FMPY_EXPORT fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) { return fmi2FullName(fmi2GetDerivatives)(c, derivatives, nx); }

#undef fmi2GetEventIndicators
FMPY_EXPORT fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) { return fmi2FullName(fmi2GetEventIndicators)(c, eventIndicators, ni); }

#undef fmi2GetContinuousStates
FMPY_EXPORT fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t nx) { return fmi2FullName(fmi2GetContinuousStates)(c, x, nx); }

#undef fmi2GetNominalsOfContinuousStates
FMPY_EXPORT fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) { return fmi2FullName(fmi2GetNominalsOfContinuousStates)(c, x_nominal, nx); }

#endif  /* MODEL_EXCHANGE */

/***************************************************
Functions for FMI 2.0 for Co-Simulation
****************************************************/

#ifdef CO_SIMULATION

/* Simulating the slave */
#undef fmi2SetRealInputDerivatives
FMPY_EXPORT fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) { return fmi2FullName(fmi2SetRealInputDerivatives)(c, vr, nvr, order, value); }

#undef fmi2GetRealOutputDerivatives
FMPY_EXPORT fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) { return fmi2FullName(fmi2GetRealOutputDerivatives)(c, vr, nvr, order, value); }

#undef fmi2DoStep
FMPY_EXPORT fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) { return fmi2FullName(fmi2DoStep)(c, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint); }

#undef fmi2CancelStep
FMPY_EXPORT fmi2Status fmi2CancelStep(fmi2Component c) { return fmi2FullName(fmi2CancelStep)(c); }

/* Inquire slave status */
#undef fmi2GetStatus
FMPY_EXPORT fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status *value) { return fmi2FullName(fmi2GetStatus)(c, s, value); }

#undef fmi2GetRealStatus
FMPY_EXPORT fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real *value) { return fmi2FullName(fmi2GetRealStatus)(c, s, value); }

#undef fmi2GetIntegerStatus
FMPY_EXPORT fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer *value) { return fmi2FullName(fmi2GetIntegerStatus)(c, s, value); }

#undef fmi2GetBooleanStatus
FMPY_EXPORT fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean *value) { return fmi2FullName(fmi2GetBooleanStatus)(c, s, value); }

#undef fmi2GetStringStatus
FMPY_EXPORT fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String *value) { return fmi2FullName(fmi2GetStringStatus)(c, s, value); }

#endif  /* CO_SIMULATION */
