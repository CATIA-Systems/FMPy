#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <conio.h>
#include <tchar.h>
#pragma comment(lib, "user32.lib")

#include <iostream>
#include <list>

using namespace std;

#include "FMI2.h"

#include "remoting_sm.h"

#define ARG(T, IDX) ((T)&pBuf[MAX_ARG_SIZE * IDX])

#define STATUS *ARG(fmi2Status*, 10)


struct LogMessage {
    std::string instanceName;
    fmi2Status status;
    std::string category;
    std::string message;
};

static std::list<LogMessage> s_logMessages;

void logMessage(FMIInstance *instance, FMIStatus status, const char *category, const char *message) {
    cout << message << endl;
    s_logMessages.push_back({ instance->name, (fmi2Status)status, category, message });
}

static void logFunctionCall(FMIInstance *instance, FMIStatus status, const char *message, ...) {

    va_list args;
    va_start(args, message);

    vprintf(message, args);

    va_end(args);

    switch (status) {
    case FMIOK:
        printf(" -> OK\n");
        break;
    case FMIWarning:
        printf(" -> Warning\n");
        break;
    case FMIDiscard:
        printf(" -> Discard\n");
        break;
    case FMIError:
        printf(" -> Error\n");
        break;
    case FMIFatal:
        printf(" -> Fatal\n");
        break;
    case FMIPending:
        printf(" -> Pending\n");
        break;
    default:
        printf(" -> Unknown status (%d)\n", status);
        break;
    }
}

HANDLE parentProcessHandle = INVALID_HANDLE_VALUE;

DWORD WINAPI watchParentProcess(LPVOID lpParam) {
	
    WaitForSingleObject(parentProcessHandle, INFINITE);

    cout << "Parent process terminated." << endl;

    exit(1);
}


int main(int argc, char *argv[]) {

    if (argc != 3) {
        cout << "Usage: server_sm <parent_process_id> <library_path>" << endl;
        return 1;
    }

    cout << "Server started" << endl;

    DWORD parentProcessId = atoi(argv[1]);

    if (parentProcessId != 0) {
            
        parentProcessHandle = OpenProcess(SYNCHRONIZE, FALSE, parentProcessId);

        cout << "parentProcessId:     " << parentProcessId << endl;
        cout << "parentProcessHandle: " << parentProcessHandle << endl;

        if (!parentProcessHandle) {
            cout << "Failed to get parent process handle." << endl;
            return 1;
        }

        DWORD dwThreadIdArray;

        HANDLE hThreadArray = CreateThread(
            NULL,                   // default security attributes
            0,                      // use default stack size  
            watchParentProcess,     // thread function name
            NULL,                   // argument to thread function 
            0,                      // use default creation flags 
            &dwThreadIdArray);      // returns the thread identifier
    }

    HANDLE inputReady = CreateEventA(
        NULL,               // default security attributes
        FALSE,              // auto-reset event object
        FALSE,              // initial state is nonsignaled
        INPUT_EVENT_NAME);  // unnamed object

    HANDLE outputReady = CreateEventA(
        NULL,               // default security attributes
        FALSE,              // auto-reset event object
        FALSE,              // initial state is nonsignaled
        OUTPUT_EVENT_NAME); // unnamed object

    HANDLE hMapFile;
    LPTSTR pBuf;

    hMapFile = CreateFileMappingA(
        INVALID_HANDLE_VALUE,    // use paging file
        NULL,                    // default security
        PAGE_READWRITE,          // read/write access
        0,                       // maximum object size (high-order DWORD)
        BUF_SIZE,                // maximum object size (low-order DWORD)
        szName);                 // name of mapping object

    if (hMapFile == NULL) {
        printf("Could not create file mapping object (%d).\n", GetLastError());
        return 1;
    }

    pBuf = (LPTSTR)MapViewOfFile(hMapFile, // handle to map object
        FILE_MAP_ALL_ACCESS,  // read/write permission
        0,
        0,
        BUF_SIZE);

    if (pBuf == NULL) {
        printf("Could not map view of file (%d).\n", GetLastError());
        CloseHandle(hMapFile);
    }

    if (!SetEvent(outputReady)) {
        printf("SetEvent failed (%d)\n", GetLastError());
        return 1;
    }

    FMIInstance *m_instance = NULL;

    bool receive = true;

    while (receive) {

        DWORD dwEvent = WaitForSingleObject(inputReady, INFINITE);

        const rpcFunction rpc = *ARG(rpcFunction *, 0);

        switch (rpc) {

        /***************************************************
        Common Functions
        ****************************************************/

        case rpc_fmi2GetTypesPlatform:
        case rpc_fmi2GetVersion:
        case rpc_fmi2SetDebugLogging:
            STATUS = fmi2Error;
            break;
        
        case rpc_fmi2Instantiate:
            m_instance = FMICreateInstance(ARG(fmi2String, 1), argv[2], logMessage, /*logFunctionCall*/NULL);
            if (!m_instance) {
                STATUS = fmi2Error;
                receive = false;
                break;
            }
            STATUS = FMI2Instantiate(m_instance, ARG(fmi2String, 4), *ARG(fmi2Type*, 2), ARG(fmi2String, 3), *ARG(fmi2Type*, 5), *ARG(fmi2Type*, 6));
            break;

        case rpc_fmi2FreeInstance:
            FMI2FreeInstance(m_instance);
            STATUS = fmi2OK;
            receive = false;
            break;

        case rpc_fmi2SetupExperiment:
            STATUS = FMI2SetupExperiment(m_instance, *ARG(fmi2Boolean*, 1), *ARG(fmi2Real*, 2), *ARG(fmi2Real*, 3), *ARG(fmi2Boolean*, 4), *ARG(fmi2Real*, 5));
            break;

        case rpc_fmi2EnterInitializationMode:
            STATUS = FMI2EnterInitializationMode(m_instance);
            break;

        case rpc_fmi2ExitInitializationMode:
            STATUS = FMI2ExitInitializationMode(m_instance);
            break;

        case rpc_fmi2Terminate:
            STATUS = FMI2Terminate(m_instance);
            break;

        case rpc_fmi2GetReal:
            STATUS = FMI2GetReal(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(fmi2Real*, 3));
            break; 
        
        case rpc_fmi2GetInteger:
            STATUS = FMI2GetInteger(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(fmi2Integer*, 3));
            break;
        
        case rpc_fmi2GetBoolean:
            STATUS = FMI2GetBoolean(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(fmi2Boolean*, 3));
            break;
        
        case rpc_fmi2GetString:
            STATUS = fmi2Error;
            break;
        
        case rpc_fmi2SetReal:
            STATUS = FMI2SetReal(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(const fmi2Real*, 3));
            break;
        
        case rpc_fmi2SetInteger:
            STATUS = FMI2SetInteger(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(const fmi2Integer*, 3));
            break;
        
        case rpc_fmi2SetBoolean:
            STATUS = FMI2SetBoolean(m_instance, ARG(fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(const fmi2Boolean*, 3));
            break;
        
        case rpc_fmi2SetString:
            STATUS = fmi2Error;
            break;

        case rpc_fmi2GetFMUstate:
        case rpc_fmi2SetFMUstate:
        case rpc_fmi2FreeFMUstate:
        case rpc_fmi2SerializedFMUstateSize:
        case rpc_fmi2SerializeFMUstate:
        case rpc_fmi2DeSerializeFMUstate:
            STATUS = fmi2Error;
            break;

        case rpc_fmi2GetDirectionalDerivative:
            STATUS = FMI2GetDirectionalDerivative(m_instance,
                ARG(const fmi2ValueReference*, 1), *ARG(size_t*, 2), 
                ARG(const fmi2ValueReference*, 3), *ARG(size_t*, 4),
                ARG(const fmi2Real*, 5), ARG(fmi2Real*, 6));
            break;

        /***************************************************
        Functions for FMI2 for Model Exchange
        ****************************************************/

        case rpc_fmi2EnterEventMode:
            STATUS = FMI2EnterEventMode(m_instance);
            break;

        case rpc_fmi2NewDiscreteStates:
            STATUS = FMI2NewDiscreteStates(m_instance, ARG(fmi2EventInfo*, 1));
            break;

        case rpc_fmi2EnterContinuousTimeMode:
            STATUS = FMI2EnterContinuousTimeMode(m_instance);
            break;

        case rpc_fmi2CompletedIntegratorStep:
            STATUS = FMI2CompletedIntegratorStep(m_instance, *ARG(fmi2Boolean*, 1), ARG(fmi2Boolean*, 2), ARG(fmi2Boolean*, 3));
            break;

        case rpc_fmi2SetTime:
            STATUS = FMI2SetTime(m_instance, *ARG(const fmi2Real*, 1));
            break;

        case rpc_fmi2SetContinuousStates:
            STATUS = FMI2SetContinuousStates(m_instance, ARG(const fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        case rpc_fmi2GetDerivatives:
            STATUS = FMI2GetDerivatives(m_instance, ARG(fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        case rpc_fmi2GetEventIndicators:
            STATUS = FMI2GetEventIndicators(m_instance, ARG(fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        case rpc_fmi2GetContinuousStates:
            STATUS = FMI2GetContinuousStates(m_instance, ARG(fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        case rpc_fmi2GetNominalsOfContinuousStates:
            STATUS = FMI2GetNominalsOfContinuousStates(m_instance, ARG(fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        /***************************************************
        Functions for FMI2 for Co-Simulation
        ****************************************************/

        case rpc_fmi2SetRealInputDerivatives:
            STATUS = FMI2SetRealInputDerivatives(m_instance, ARG(const fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(const fmi2Integer*, 3), ARG(const fmi2Real*, 4));
            break;

        case rpc_fmi2GetRealOutputDerivatives:
            STATUS = FMI2GetRealOutputDerivatives(m_instance, ARG(const fmi2ValueReference*, 1), *ARG(size_t*, 2), ARG(const fmi2Integer*, 3), ARG(fmi2Real*, 4));
            break;

        case rpc_fmi2DoStep:
            STATUS = FMI2DoStep(m_instance, *ARG(fmi2Real*, 1), *ARG(fmi2Real*, 2), *ARG(fmi2Boolean*, 3));
            break;

        case rpc_fmi2CancelStep:
            STATUS = FMI2CancelStep(m_instance);
            break;

        case rpc_fmi2GetStatus:
            STATUS = FMI2GetStatus(m_instance, *ARG(fmi2StatusKind*, 1), ARG(fmi2Status*, 2));
            break;

        case rpc_fmi2GetRealStatus:
            STATUS = FMI2GetRealStatus(m_instance, *ARG(fmi2StatusKind*, 1), ARG(fmi2Real*, 2));
            break;

        case rpc_fmi2GetIntegerStatus:
            STATUS = FMI2GetIntegerStatus(m_instance, *ARG(fmi2StatusKind*, 1), ARG(fmi2Integer*, 2));
            break;

        case rpc_fmi2GetBooleanStatus:
            STATUS = FMI2GetBooleanStatus(m_instance, *ARG(fmi2StatusKind*, 1), ARG(fmi2Boolean*, 2));
            break;

        case rpc_fmi2GetStringStatus:
            STATUS = FMI2GetContinuousStates(m_instance, ARG(fmi2Real*, 1), *ARG(size_t*, 2));
            break;

        default:
            cout << "Unknown RPC: " << rpc << endl;
            STATUS = fmi2Fatal;
            receive = false;
            break;
        }

        if (!SetEvent(outputReady)) {
            printf("SetEvent failed (%d)\n", GetLastError());
            exit(1);
        }

    }

    UnmapViewOfFile(pBuf);
    CloseHandle(hMapFile);

    CloseHandle(inputReady);
    CloseHandle(outputReady);

    return 0;
}
