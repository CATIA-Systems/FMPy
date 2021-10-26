#include <windows.h>
#include <stdio.h>
#include <conio.h>
#include <tchar.h>

#include <string>
#include <iostream>

using namespace std;

#include "fmi2Functions.h"

#include "remoting_sm.h"

#define ARG(IDX) (&pBuf[MAX_ARG_SIZE * IDX])


HANDLE inputReady = INVALID_HANDLE_VALUE;
HANDLE outputReady = INVALID_HANDLE_VALUE;

HANDLE hMapFile = INVALID_HANDLE_VALUE;
LPTSTR pBuf = NULL;

fmi2CallbackLogger s_logger = NULL;
fmi2ComponentEnvironment s_componentEnvironment = NULL;

static 	PROCESS_INFORMATION s_proccessInfo = { 0 };

#define NOT_IMPLEMENTED return fmi2Error;


static fmi2Status makeRPC(rpcFunction rpc) {

    fmi2Status status = (fmi2Status)-1;

    memcpy(ARG(0), &rpc, sizeof(rpcFunction));
    memcpy(ARG(10), &status, sizeof(fmi2Status));

    DWORD dwEvent = SignalObjectAndWait(inputReady, outputReady, INFINITE, TRUE);

    status = *((fmi2Status*)ARG(10));

    // wait until shared memory has been updated
    while (status < fmi2OK) {
        status = *((fmi2Status*)ARG(10));
    }

    return status;
}

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

////static void forwardLogMessages(const list<LogMessage> &logMessages) {
////	for (auto it = logMessages.begin(); it != logMessages.end(); it++) {
////		auto &m = *it;
////		s_logger(s_componentEnvironment, m.instanceName.c_str(), fmi2Status(m.status), m.category.c_str(), m.message.c_str());
////	}
////}
////
////static fmi2Status handleReturnValue(ReturnValue r) {
////	forwardLogMessages(r.logMessages);
////	return fmi2Status(r.status);
////}
//
//fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn,	size_t nCategories,	const fmi2String categories[]) {
//	NOT_IMPLEMENTED
//}
//
//
//static void handleLogMessages(msgpack_object_array logMessages) {
//
//    for (int i = 0; i < logMessages.size; i++) {
//        auto m = logMessages.ptr[i].via.array;
//        auto instanceName = m.ptr[0].via.str.ptr;
//        auto status = m.ptr[1].via.i64;
//        auto category = m.ptr[2].via.str.ptr;
//        auto message = m.ptr[3].via.str.ptr;
//        s_logger(s_componentEnvironment, instanceName, (fmi2Status)status, category, message);
//    }
//}

/* Creation and destruction of FMU instances and setting debug status */
fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID, fmi2String fmuResourceLocation, const fmi2CallbackFunctions* functions, fmi2Boolean visible, fmi2Boolean loggingOn) {

    if (!functions || !functions->logger) {
        return NULL;
    }

    s_logger = functions->logger;
    s_componentEnvironment = functions->componentEnvironment;

    inputReady = CreateEvent(
        NULL,              // default security attributes
        FALSE,             // auto-reset event object
        FALSE,             // initial state is nonsignaled
        INPUT_EVENT_NAME); // unnamed object

    outputReady = CreateEvent(
        NULL,               // default security attributes
        FALSE,              // auto-reset event object
        FALSE,              // initial state is nonsignaled
        OUTPUT_EVENT_NAME); // unnamed object

    char path[MAX_PATH];

    HMODULE hm = NULL;

    if (GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCSTR)&fmi2GetTypesPlatform, &hm) == 0) {
        s_logger(s_componentEnvironment, instanceName, fmi2Error, "error", "GetModuleHandle failed, error = %d.", GetLastError());
        return NULL;
    }

    if (GetModuleFileName(hm, path, sizeof(path)) == 0) {
        s_logger(s_componentEnvironment, instanceName, fmi2Error, "error", "GetModuleFileName failed, error = %d.", GetLastError());
        return NULL;
    }

    const string filename(path);

    const string modelIdentifier = filename.substr(filename.find_last_of('\\') + 1, filename.find_last_of('.') - filename.find_last_of('\\') - 1);

    if (!modelIdentifier.compare("client_sm")) {

        s_logger(s_componentEnvironment, instanceName, fmi2OK, "info", "Remoting server started externally.");

    } else {

        DWORD currentProcessId = GetCurrentProcessId();

        const string platformPath = filename.substr(0, filename.find_last_of('\\'));

        const string binariesPath = platformPath.substr(0, platformPath.find_last_of('\\'));

        const string command = binariesPath + "\\win32\\server_sm.exe " + to_string(currentProcessId) + " " + binariesPath + "\\win32\\" + modelIdentifier + ".dll";

        // additional information
        STARTUPINFO si;

        // set the size of the structures
        ZeroMemory(&si, sizeof(si));
        si.cb = sizeof(si);
        ZeroMemory(&s_proccessInfo, sizeof(s_proccessInfo));

        s_logger(s_componentEnvironment, instanceName, fmi2OK, "info", "Starting remoting server. Command: %s", command.c_str());

        // start the program up
        const BOOL success = CreateProcessA(NULL, // the path
            (LPSTR)command.c_str(),               // command line
            NULL,                                 // process handle not inheritable
            NULL,                                 // thread handle not inheritable
            FALSE,                                // set handle inheritance to FALSE
            0, // CREATE_NO_WINDOW,                     // creation flags
            NULL,                                 // use parent's environment block
            NULL,                                 // use parent's starting directory 
            &si,                                  // pointer to STARTUPINFO structure
            &s_proccessInfo                       // pointer to PROCESS_INFORMATION structure
        );

        if (success) {
            s_logger(s_componentEnvironment, instanceName, fmi2OK, "info", "Server process id is %d.", s_proccessInfo.dwProcessId);
        } else {
            s_logger(s_componentEnvironment, instanceName, fmi2Error, "error", "Failed to start server.");
            return nullptr;
        }

        WaitForSingleObject(outputReady, INFINITE);
    }

    hMapFile = OpenFileMapping(
        FILE_MAP_ALL_ACCESS,   // read/write access
        FALSE,                 // do not inherit the name
        szName);               // name of mapping object

    if (hMapFile == NULL) {
        s_logger(s_componentEnvironment, instanceName, fmi2Error, "error", "Could not open file mapping object (%d).", GetLastError());
        return NULL;
    }

    pBuf = (LPTSTR)MapViewOfFile(hMapFile, FILE_MAP_ALL_ACCESS, 0, 0, BUF_SIZE);

    if (pBuf == NULL) {
        s_logger(s_componentEnvironment, instanceName, fmi2Error, "error", "Could not map view of file (%d).", GetLastError());
        CloseHandle(hMapFile);
        return NULL;
    }

    strncpy(ARG(1), instanceName, 1024);
    memcpy(ARG(2), &fmuType, sizeof(fmi2Type));
    strncpy(ARG(3), fmuGUID, 1024);
    strncpy(ARG(4), fmuResourceLocation, 1024);
    memcpy(ARG(5), &visible, sizeof(fmi2Boolean));
    memcpy(ARG(6), &loggingOn, sizeof(fmi2Boolean));

    fmi2Status status = makeRPC(rpc_fmi2Instantiate);

    if (status > fmi2Warning) {
        return NULL;
    }

    return (fmi2Component)0x1;
}

void fmi2FreeInstance(fmi2Component c) {

    fmi2Status status = makeRPC(rpc_fmi2FreeInstance);

    UnmapViewOfFile(pBuf);

    CloseHandle(hMapFile);

    CloseHandle(inputReady);
    CloseHandle(outputReady);
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) {

    memcpy(ARG(1), &toleranceDefined, sizeof(fmi2Boolean));
    memcpy(ARG(2), &tolerance, sizeof(fmi2Real));
    memcpy(ARG(3), &startTime, sizeof(fmi2Real));
    memcpy(ARG(4), &stopTimeDefined, sizeof(fmi2Boolean));
    memcpy(ARG(5), &stopTime, sizeof(fmi2Real));

    fmi2Status status = makeRPC(rpc_fmi2SetupExperiment);

    return status;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) {
    return makeRPC(rpc_fmi2EnterInitializationMode);
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c) {
    return makeRPC(rpc_fmi2ExitInitializationMode);
}

fmi2Status fmi2Terminate(fmi2Component c) {
    return makeRPC(rpc_fmi2Terminate);
}

fmi2Status fmi2Reset(fmi2Component c) {
    return makeRPC(rpc_fmi2Reset);
}

/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
    
    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetReal);

    memcpy(value, ARG(3), sizeof(fmi2Real) * nvr);

    return status;
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
    
    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetInteger);

    memcpy(value, ARG(3), sizeof(fmi2Integer) * nvr);

    return status;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {
    
    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetBoolean);

    memcpy(value, ARG(3), sizeof(fmi2Boolean) * nvr);

    return status;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {
	NOT_IMPLEMENTED
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {

    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));
    memcpy(ARG(3), value, sizeof(fmi2Real) * nvr);

    return makeRPC(rpc_fmi2SetReal);
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {

    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));
    memcpy(ARG(3), value, sizeof(fmi2Integer) * nvr);

    return makeRPC(rpc_fmi2SetInteger);
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {

    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));
    memcpy(ARG(3), value, sizeof(fmi2Boolean) * nvr);

    return makeRPC(rpc_fmi2SetBoolean);
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
    
    memcpy(ARG(1), vUnknown_ref, sizeof(fmi2ValueReference) * nUnknown);
    memcpy(ARG(2), &nUnknown, sizeof(size_t));
    memcpy(ARG(3), vKnown_ref, sizeof(fmi2ValueReference) * nKnown);
    memcpy(ARG(4), &nKnown, sizeof(size_t));
    memcpy(ARG(5), dvKnown, sizeof(fmi2Real) * nKnown);

    fmi2Status status = makeRPC(rpc_fmi2GetDirectionalDerivative);

    memcpy(dvUnknown, ARG(6), sizeof(fmi2Real) * nKnown);

    return status;
}

/***************************************************
Types for Functions for FMI2 for Model Exchange
****************************************************/

/* Enter and exit the different modes */
fmi2Status fmi2EnterEventMode(fmi2Component c) {
    return makeRPC(rpc_fmi2EnterEventMode);
}

fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) {
    
    fmi2Status status = makeRPC(rpc_fmi2NewDiscreteStates);

    memcpy(eventInfo, ARG(1), sizeof(fmi2EventInfo));

    return status;
}

fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {
    return makeRPC(rpc_fmi2EnterContinuousTimeMode);
}

fmi2Status fmi2CompletedIntegratorStep(fmi2Component c,	fmi2Boolean  noSetFMUStatePriorToCurrentPoint, fmi2Boolean* enterEventMode, fmi2Boolean* terminateSimulation) {
    
    memcpy(ARG(1), &noSetFMUStatePriorToCurrentPoint, sizeof(fmi2Boolean));

    fmi2Status status = makeRPC(rpc_fmi2CompletedIntegratorStep);

    memcpy(enterEventMode,      ARG(2), sizeof(fmi2Boolean));
    memcpy(terminateSimulation, ARG(3), sizeof(fmi2Boolean));

    return status;
}

/* Providing independent variables and re-initialization of caching */
fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {

    memcpy(ARG(1), &time, sizeof(fmi2Real));

    return makeRPC(rpc_fmi2EnterEventMode);
}

fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) {

    memcpy(ARG(1), x, sizeof(fmi2Real) * nx);
    memcpy(ARG(2), &nx, sizeof(size_t));

    return makeRPC(rpc_fmi2SetContinuousStates);
}

/* Evaluation of the model equations */
fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {

    memcpy(ARG(2), &nx, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetDerivatives);

    memcpy(derivatives, ARG(1), sizeof(fmi2Real) * nx);

    return status;
}

fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {
    
    memcpy(ARG(2), &ni, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetEventIndicators);

    memcpy(eventIndicators, ARG(1), sizeof(fmi2Real) * ni);

    return status;
}

fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t nx) {
    
    memcpy(ARG(2), &nx, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetContinuousStates);

    memcpy(x, ARG(1), sizeof(fmi2Real) * nx);

    return status;
}

fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {
    
    memcpy(ARG(2), &nx, sizeof(size_t));

    fmi2Status status = makeRPC(rpc_fmi2GetNominalsOfContinuousStates);

    memcpy(x_nominal, ARG(1), sizeof(fmi2Real) * nx);

    return status;
}

/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) {
    NOT_IMPLEMENTED
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) {
    
    memcpy(ARG(1), vr, sizeof(fmi2ValueReference) * nvr);
    memcpy(ARG(2), &nvr, sizeof(size_t));
    memcpy(ARG(3), order, sizeof(fmi2Integer) * nvr);

    fmi2Status status = makeRPC(rpc_fmi2GetRealOutputDerivatives);

    memcpy(value, ARG(4), sizeof(fmi2Real) * nvr);

    return status;
}

fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
    
    memcpy(ARG(1), &currentCommunicationPoint, sizeof(fmi2Real));
    memcpy(ARG(2), &communicationStepSize, sizeof(fmi2Real));
    memcpy(ARG(3), &noSetFMUStatePriorToCurrentPoint, sizeof(fmi2Boolean));

    return makeRPC(rpc_fmi2DoStep);
}

fmi2Status fmi2CancelStep(fmi2Component c) {
    return makeRPC(rpc_fmi2CancelStep);
}

/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {
    
    memcpy(ARG(1), &s, sizeof(fmi2StatusKind));

    fmi2Status status = makeRPC(rpc_fmi2GetStatus);

    memcpy(value, ARG(2), sizeof(fmi2Status));

    return status;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {

    memcpy(ARG(1), &s, sizeof(fmi2StatusKind));

    fmi2Status status = makeRPC(rpc_fmi2GetRealStatus);

    memcpy(value, ARG(2), sizeof(fmi2Real));

    return status;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {

    memcpy(ARG(1), &s, sizeof(fmi2StatusKind));

    fmi2Status status = makeRPC(rpc_fmi2GetIntegerStatus);

    memcpy(value, ARG(2), sizeof(fmi2Integer));

    return status;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {

    memcpy(ARG(1), &s, sizeof(fmi2StatusKind));

    fmi2Status status = makeRPC(rpc_fmi2GetBooleanStatus);

    memcpy(value, ARG(2), sizeof(fmi2Boolean));

    return status;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String*  value) {

    memcpy(ARG(1), &s, sizeof(fmi2StatusKind));

    fmi2Status status = makeRPC(rpc_fmi2GetStringStatus);

    *value = ARG(2);

    return status;
}
