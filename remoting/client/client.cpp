#include "rpc/client.h"
#include <iostream>
#include <vector>
#include "Windows.h"
#include "Shlwapi.h"
#include "remoting.h"

extern "C" {
#include "fmi2Functions.h"
}

using namespace std;

using double_vector = vector<double>;


static void functionInThisDll() {}

static rpc::client *client = nullptr;

static 	PROCESS_INFORMATION s_proccessInfo;

static fmi2CallbackLogger s_logger = nullptr;

#define NOT_IMPLEMENTED return fmi2Error;


/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
const char* fmi2GetTypesPlatform() {
	return fmi2TypesPlatform;
}

const char* fmi2GetVersion() {
	return fmi2Version;
}

static void forwardLogMessages(const list<LogMessage> &logMessages) {
	for (auto it = logMessages.begin(); it != logMessages.end(); it++) {
		auto &m = *it;
		s_logger(NULL, m.instanceName.c_str(), fmi2Status(m.status), m.category.c_str(), m.message.c_str());
	}
}

static fmi2Status handleReturnValue(ReturnValue r) {
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,	size_t nCategories,	const fmi2String categories[]) {
	NOT_IMPLEMENTED
}

/* Creation and destruction of FMU instances and setting debug status */
fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID, fmi2String fmuResourceLocation, const fmi2CallbackFunctions* functions, fmi2Boolean visible, fmi2Boolean loggingOn) {
	
	s_logger = functions->logger;

	char path[MAX_PATH];
	char win32DllPath[MAX_PATH];
	HMODULE hm = NULL;

	if (GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
		GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
		(LPCSTR)&functionInThisDll, &hm) == 0)
	{
		int ret = GetLastError();
		//fprintf(stderr, "GetModuleHandle failed, error = %d\n", ret);
		// Return or however you want to handle an error.
	}
	if (GetModuleFileName(hm, path, sizeof(path)) == 0)
	{
		int ret = GetLastError();
		//fprintf(stderr, "GetModuleFileName failed, error = %d\n", ret);
		// Return or however you want to handle an error.
	}

	char drive[_MAX_DRIVE];
	char dir[_MAX_DIR];
	char fname[_MAX_FNAME];
	char ext[_MAX_EXT];

	_splitpath(path, drive, dir, fname, ext);

	if (strcmp(fname, "client") == 0) {
		functions->logger(NULL, instanceName, fmi2OK, "info", "Server started externally.");
	} else {
		PathRemoveFileSpec(path);

		// build the 32-bit DLL path
		strcpy(win32DllPath, path);
		PathRemoveFileSpec(win32DllPath);
		PathAppend(win32DllPath, "win32");
		PathAppend(win32DllPath, fname);
		strcat(win32DllPath, ".dll");

		// build the server.exe path
		PathAppend(path, "server.exe");

		cout << path << endl;

		char lpCommandLine[32767];

		strcpy(lpCommandLine, path);
		strcat(lpCommandLine, " ");
		strcat(lpCommandLine, win32DllPath);
		//strcat(lpCommandLine, "\"");

		//LPSTR lpCommandLine_ = "E:\\Development\\FMPy\\wrapper\\server\\build\\Debug\\server.exe E:\\Development\\Reference-FMUs\\build\\temp\\BouncingBall\\binaries\\win32\\BouncingBall.dll";

		// additional information
		STARTUPINFO si;

		// set the size of the structures
		ZeroMemory(&si, sizeof(si));
		si.cb = sizeof(si);
		ZeroMemory(&s_proccessInfo, sizeof(s_proccessInfo));

		functions->logger(NULL, "inst", fmi2OK, "info", lpCommandLine);

		// start the program up
		auto p = CreateProcess(NULL,   // the path
			lpCommandLine,        // Command line
			NULL,           // Process handle not inheritable
			NULL,           // Thread handle not inheritable
			FALSE,          // Set handle inheritance to FALSE
			0,              // No creation flags
			NULL,           // Use parent's environment block
			NULL,           // Use parent's starting directory 
			&si,            // Pointer to STARTUPINFO structure
			&s_proccessInfo // Pointer to PROCESS_INFORMATION structure (removed extra parentheses)
		);

	}

	client = new rpc::client("localhost", rpc::constants::DEFAULT_PORT);
	auto r = client->call("fmi2Instantiate", instanceName, (int)fmuType, fmuGUID, fmuResourceLocation, visible, loggingOn).as<ReturnValue>();
	forwardLogMessages(r.logMessages);
	return fmi2Component(r.status);
}

void fmi2FreeInstance(fmi2Component c) {
	client->call("fmi2FreeInstance");

	//// Close process and thread handles
	//CloseHandle(s_proccessInfo.hProcess);
	//CloseHandle(s_proccessInfo.hThread);
	auto s = TerminateProcess(s_proccessInfo.hProcess, EXIT_SUCCESS);
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) {
	auto r = client->call("fmi2SetupExperiment", toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) {
	auto r = client->call("fmi2EnterInitializationMode").as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c) {
	auto r = client->call("fmi2ExitInitializationMode").as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2Terminate(fmi2Component c) {
	auto r = client->call("fmi2Terminate").as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2Reset(fmi2Component c) {
	auto r = client->call("fmi2Reset").as<ReturnValue>();
	return handleReturnValue(r);
}

/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
	vector<unsigned int> v_vr(vr, vr + nvr);
	auto r = client->call("fmi2GetReal", v_vr).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), value);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
	vector<unsigned int> v_vr(vr, vr + nvr);
	auto r = client->call("fmi2GetInteger", v_vr).as<IntegerReturnValue>();
	copy(r.value.begin(), r.value.end(), value);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {
	vector<unsigned int> v_vr(vr, vr + nvr);
	auto r = client->call("fmi2GetBoolean", v_vr).as<IntegerReturnValue>();
	copy(r.value.begin(), r.value.end(), value);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {
	auto vr_ = static_cast<const unsigned int*>(vr);
	vector<unsigned int> v_vr(vr_, vr_ + nvr);
	vector<double> v_value(value, value + nvr);
	auto r = client->call("fmi2SetReal", v_vr, v_value).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
	auto vr_ = static_cast<const unsigned int*>(vr);
	vector<unsigned int> v_vr(vr_, vr_ + nvr);
	vector<int> v_value(value, value + nvr);
	auto r = client->call("fmi2SetInteger", v_vr, v_value).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {
	auto vr_ = static_cast<const unsigned int*>(vr);
	vector<unsigned int> v_vr(vr_, vr_ + nvr);
	vector<int> v_value(value, value + nvr);
	auto r = client->call("fmi2SetBoolean", v_vr, v_value).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]) {
	NOT_IMPLEMENTED
}

/* Getting and setting the internal FMU state */
fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t* size) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte[], size_t size) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
	NOT_IMPLEMENTED
}

/* Getting partial derivatives */
fmi2Status fmi2GetDirectionalDerivative(fmi2Component c, const fmi2ValueReference vUnknown_ref[], size_t nUnknown, const fmi2ValueReference vKnown_ref[], size_t nKnown, const fmi2Real dvKnown[], fmi2Real dvUnknown[]) {
	NOT_IMPLEMENTED
}

/***************************************************
Types for Functions for FMI2 for Model Exchange
****************************************************/

/* Enter and exit the different modes */
fmi2Status fmi2EnterEventMode(fmi2Component c) {
	auto r = client->call("fmi2EnterEventMode").as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) {
	//auto r = client->call("fmi2NewDiscreteStates").as<EventInfoReturnValue>();
	//eventInfo->newDiscreteStatesNeeded           = r.newDiscreteStatesNeeded;
	//eventInfo->terminateSimulation               = r.terminateSimulation;
	//eventInfo->nominalsOfContinuousStatesChanged = r.nominalsOfContinuousStatesChanged;
	//eventInfo->valuesOfContinuousStatesChanged   = r.valuesOfContinuousStatesChanged;
	//eventInfo->nextEventTimeDefined              = r.nextEventTimeDefined;
	//eventInfo->nextEventTime                     = r.nextEventTime;
	eventInfo->newDiscreteStatesNeeded = 0;
	eventInfo->terminateSimulation = 0;
	eventInfo->nominalsOfContinuousStatesChanged = 0;
	eventInfo->valuesOfContinuousStatesChanged = 0;
	eventInfo->nextEventTimeDefined = 0;
	eventInfo->nextEventTime = 0;
	//forwardLogMessages(r.logMessages);
	return fmi2Status(fmi2OK);
}

fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {
	auto r = client->call("fmi2EnterContinuousTimeMode").as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2CompletedIntegratorStep(fmi2Component c,	fmi2Boolean  noSetFMUStatePriorToCurrentPoint, fmi2Boolean* enterEventMode, fmi2Boolean* terminateSimulation) {
	auto r = client->call("fmi2CompletedIntegratorStep", noSetFMUStatePriorToCurrentPoint).as<IntegerReturnValue>();
	*enterEventMode = r.value[0];
	*terminateSimulation = r.value[1];
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

/* Providing independent variables and re-initialization of caching */
fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {
	auto r = client->call("fmi2SetTime", time).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) {
	vector<double> _x(x, x + nx);
	auto r = client->call("fmi2SetContinuousStates", _x).as<ReturnValue>();
	return handleReturnValue(r);
}

/* Evaluation of the model equations */
fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {
	auto r = client->call("fmi2GetDerivatives", nx).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), derivatives);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {
	auto r = client->call("fmi2GetEventIndicators", ni).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), eventIndicators);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t nx) {
	auto r = client->call("fmi2GetContinuousStates", nx).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), x);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {
	auto r = client->call("fmi2GetNominalsOfContinuousStates", nx).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), x_nominal);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) {
	auto vr_ = static_cast<const unsigned int*>(vr);
	vector<unsigned int> v_vr(vr_, vr_ + nvr);
	vector<int> v_order(order, order + nvr);
	vector<double> v_value(value, value + nvr);
	auto r = client->call("fmi2SetRealInputDerivatives", v_vr, v_order, v_value).as<ReturnValue>();
	return handleReturnValue(r);
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) {
	vector<unsigned int> v_vr(vr, vr + nvr);
	vector<int> v_order(order, order + nvr);
	auto r = client->call("fmi2GetRealOutputDerivatives", v_vr, v_order).as<RealReturnValue>();
	copy(r.value.begin(), r.value.end(), value);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
	auto r = client->call("fmi2DoStep", double(currentCommunicationPoint), double(communicationStepSize), int(noSetFMUStatePriorToCurrentPoint)).as<ReturnValue>();
	return handleReturnValue(r);
}

/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {
	auto r = client->call("fmi2GetStatus", int(s)).as<IntegerReturnValue>();
	*value = fmi2Status(r.value[0]);
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {
	auto r = client->call("fmi2GetRealStatus", int(s)).as<RealReturnValue>();
	*value = r.value[0];
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
	auto r = client->call("fmi2GetIntegerStatus", int(s)).as<IntegerReturnValue>();
	*value = r.value[0];
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
	auto r = client->call("fmi2GetBooleanStatus", int(s)).as<IntegerReturnValue>();
	*value = r.value[0];
	forwardLogMessages(r.logMessages);
	return fmi2Status(r.status);
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String*  value) {
	NOT_IMPLEMENTED
}
