#ifdef _WIN32
#include <Windows.h>
#else
#include <pthread.h>
#include <unistd.h>
#include <fcntl.h>
#define MAX_PATH 2048
#endif

#include <stdarg.h>
#include <time.h>
#include <list>
#include <iostream>
#include <stdexcept>

#include "rpc/server.h"

#include "remoting_tcp.h"

extern "C" {
#include "FMI2.h"
}

using namespace std;

#define NOT_IMPLEMENTED return static_cast<int>(fmi2Error);

static list<LogMessage> s_logMessages;

static rpc::server *s_server = nullptr;

time_t s_lastActive;

void logMessage(FMIInstance *instance, FMIStatus status, const char *category, const char *message) {
	s_logMessages.push_back({instance->name, status, category, message});
}

static void resetExitTimer() {
	time(&s_lastActive);
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

static const char *lockFile = NULL;


#ifdef _WIN32
DWORD WINAPI checkLockFile(LPVOID lpParam) {

    HANDLE hLockFile = INVALID_HANDLE_VALUE;

    while (hLockFile == INVALID_HANDLE_VALUE) {
        Sleep(500);
        hLockFile = CreateFileA(
            lockFile,       // lpFileName
            GENERIC_WRITE,  // dwDesiredAccess
            0,              // dwShareMode
            0,              // lpSecurityAttributes
            CREATE_ALWAYS,  // dwCreationDisposition
            0,              // dwFlagsAndAttributes
            0               // hTemplateFile
        );
    }

    cout << "Lock file " << lockFile << " open. Exiting." << endl;
    
    s_server->stop();
    
    return 0;
}
#else
void *checkLockFile(void *arg) {

    FILE* hLockFile = NULL;

    while (!hLockFile) {
        usleep(500000);
        hLockFile = fopen(lockFile, "w");
    }

    cout << "Lock file open. Exiting." << endl;

    s_server->stop();

    return NULL;
}
#endif		



class FMU {

private:

    string libraryPath;

#ifdef _WIN32
	HMODULE libraryHandle = nullptr;
#else
    void *libraryHandle = nullptr;
#endif

	ReturnValue createReturnValue(int status) {
		ReturnValue r = { status, s_logMessages };
		s_logMessages.clear();
		return r;
	}

	RealReturnValue createRealReturnValue(int status, const vector<double> &value) {
		RealReturnValue r = { status, s_logMessages, value };
		s_logMessages.clear();
		return r;
	}

	IntegerReturnValue createIntegerReturnValue(int status, const vector<int> &value) {
		IntegerReturnValue r = { status, s_logMessages, value };
		s_logMessages.clear();
		return r;
	}

	EventInfoReturnValue createEventInfoReturnValue(int status, const fmi2EventInfo *eventInfo) {
		EventInfoReturnValue r = {
			status,
			s_logMessages,
			eventInfo->newDiscreteStatesNeeded, 
			eventInfo->terminateSimulation,
			eventInfo->nominalsOfContinuousStatesChanged,
			eventInfo->valuesOfContinuousStatesChanged,
			eventInfo->nextEventTimeDefined,
			eventInfo->nextEventTime,
		};
		s_logMessages.clear();
		return r;
	}

public:
	rpc::server srv;

    FMIInstance *m_instance;

	FMU(const string &libraryPath) : srv(rpc::constants::DEFAULT_PORT) {

        this->libraryPath = libraryPath;
		
		srv.bind("echo", [](string const& s) {
			return s;
		});

        srv.bind("sum", [this](double a, double b) {
            return a + b;
        });

		srv.bind("fmi2SetDebugLogging", [this]() { 
            NOT_IMPLEMENTED
        });

		/* Creation and destruction of FMU instances and setting debug status */
		srv.bind("fmi2Instantiate", [this](string const& instanceName, int fmuType, string const& fmuGUID, string const& fmuResourceLocation, int visible, int loggingOn) {

            m_instance = FMICreateInstance(instanceName.c_str(), this->libraryPath.c_str(), logMessage, nullptr);

            if (!m_instance) {
                return createReturnValue(0);
            }

			resetExitTimer();

            fmi2Status status = FMI2Instantiate(m_instance, fmuResourceLocation.c_str(), static_cast<fmi2Type>(fmuType), fmuGUID.c_str(), visible, loggingOn);

            if (status > fmi2Warning) {
                return createReturnValue(0);
            }
			
            long int_value = reinterpret_cast<long>(m_instance);
            
            return createReturnValue(static_cast<int>(int_value));
		});

		srv.bind("fmi2FreeInstance", [this]() { 
			resetExitTimer();
			FMI2FreeInstance(m_instance);
		});

		/* Enter and exit initialization mode, terminate and reset */
		srv.bind("fmi2SetupExperiment", [this](int toleranceDefined, double tolerance, double startTime, int stopTimeDefined, double stopTime) {
			resetExitTimer();
			const fmi2Status status = FMI2SetupExperiment(m_instance, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2EnterInitializationMode", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2EnterInitializationMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2ExitInitializationMode",  [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2ExitInitializationMode(m_instance);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2Terminate", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2Terminate(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2Reset", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2Reset(m_instance);
			return createReturnValue(status);
		});

		/* Getting and setting variable values */
		srv.bind("fmi2GetReal", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<double> value(vr.size());
			const fmi2Status status = FMI2GetReal(m_instance, vr.data(), vr.size(), value.data());
            return createRealReturnValue(status, value);
		});

		srv.bind("fmi2GetInteger", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<int> value(vr.size());
			const fmi2Status status = FMI2GetInteger(m_instance, vr.data(), vr.size(), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetBoolean", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<int> value(vr.size());
			const fmi2Status status = FMI2GetBoolean(m_instance, vr.data(), vr.size(), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2SetReal", [this](const vector<unsigned int> &vr, const vector<double> &value) {
			resetExitTimer();
			const fmi2Status status = FMI2SetReal(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2SetInteger", [this](const vector<unsigned int> &vr, const vector<int> &value) {
			resetExitTimer();
			const fmi2Status status = FMI2SetInteger(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2SetBoolean", [this](const vector<unsigned int> &vr, const vector<int> &value) {
			resetExitTimer();
			const fmi2Status status = FMI2SetBoolean(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		/* Getting and setting the internal FMU state */
		// fmi2GetFMUstateTYPE *m_fmi2Component c, fmi2FMUstate* FMUstate);
		// fmi2SetFMUstateTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate);
		// fmi2FreeFMUstateTYPE *m_fmi2Component c, fmi2FMUstate* FMUstate);
		// fmi2SerializedFMUstateSizeTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate, size_t* size);
		// fmi2SerializeFMUstateTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte[], size_t size);
		// fmi2DeSerializeFMUstateTYPE *m_fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate);

		srv.bind("fmi2GetDirectionalDerivative", [this](const vector<unsigned int> &vUnknown_ref, const vector<unsigned int> &vKnown_ref, const vector<double> &dvKnown) {
			resetExitTimer();
			vector<double> dvUnknown(vKnown_ref.size());
			const fmi2Status status = FMI2GetDirectionalDerivative(m_instance, vUnknown_ref.data(), vUnknown_ref.size(),
				vKnown_ref.data(), vKnown_ref.size(), dvKnown.data(), dvUnknown.data());
			return createRealReturnValue(status, dvUnknown);
		});

		/***************************************************
		Types for Functions for FMI2 for Model Exchange
		****************************************************/

		/* Enter and exit the different modes */
		srv.bind("fmi2EnterEventMode", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2EnterEventMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2NewDiscreteStates", [this]() {
			resetExitTimer();
			fmi2EventInfo eventInfo = { 0 };
			const fmi2Status status = FMI2NewDiscreteStates(m_instance, &eventInfo);
			return createEventInfoReturnValue(status, &eventInfo);
		});

		srv.bind("fmi2EnterContinuousTimeMode", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2EnterContinuousTimeMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2CompletedIntegratorStep", [this](int noSetFMUStatePriorToCurrentPoint) {
			resetExitTimer();
			vector<int> value(2);
			fmi2Boolean* enterEventMode = &(value.data()[0]);
			fmi2Boolean* terminateSimulation = &(value.data()[1]);
			const fmi2Status status = FMI2CompletedIntegratorStep(m_instance, noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation);
			return createIntegerReturnValue(status, value);
		});

		/* Providing independent variables and re-initialization of caching */
		srv.bind("fmi2SetTime", [this](double time) {
			resetExitTimer();
			const fmi2Status status = FMI2SetTime(m_instance, time);
			return createReturnValue(status);
		});

		srv.bind("fmi2SetContinuousStates", [this](const vector<double> &x) {
			resetExitTimer();
			const fmi2Status status = FMI2SetContinuousStates(m_instance, x.data(), x.size());
			return createReturnValue(status);
		});

		/* Evaluation of the model equations */
		srv.bind("fmi2GetDerivatives", [this](size_t nx) {
			resetExitTimer();
			vector<double> derivatives(nx);
			const fmi2Status status = FMI2GetDerivatives(m_instance, derivatives.data(), nx);
			return createRealReturnValue(status, derivatives);
		});
		
		srv.bind("fmi2GetEventIndicators", [this](size_t ni) {
			resetExitTimer();
			vector<double> eventIndicators(ni);
			const fmi2Status status = FMI2GetEventIndicators(m_instance, eventIndicators.data(), ni);
			return createRealReturnValue(status, eventIndicators);
		});

		srv.bind("fmi2GetContinuousStates", [this](size_t nx) {
			resetExitTimer();
			vector<double> x(nx);
			const fmi2Status status = FMI2GetContinuousStates(m_instance, x.data(), nx);
			return createRealReturnValue(status, x);
		});

		srv.bind("fmi2GetNominalsOfContinuousStates", [this](size_t nx) {
			resetExitTimer();
			vector<double> x_nominal(nx);
			const fmi2Status status = FMI2GetNominalsOfContinuousStates(m_instance, x_nominal.data(), nx);
			return createRealReturnValue(status, x_nominal);
		});

		/***************************************************
		Types for Functions for FMI2 for Co-Simulation
		****************************************************/

		/* Simulating the slave */
		srv.bind("fmi2SetRealInputDerivatives", [this](const vector<unsigned int> &vr, const vector<int> &order, const vector<double> &value) {
			resetExitTimer();
			const fmi2Status status = FMI2SetRealInputDerivatives(m_instance, vr.data(), vr.size(), order.data(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2GetRealOutputDerivatives", [this](const vector<unsigned int> &vr, const vector<int> &order) {
			resetExitTimer();
			vector<double> value(vr.size());
			const fmi2Status status = FMI2GetRealOutputDerivatives(m_instance, vr.data(), vr.size(), order.data(), value.data());
			return createRealReturnValue(status, value);
		});

		srv.bind("fmi2DoStep", [this](double currentCommunicationPoint, double communicationStepSize, int noSetFMUStatePriorToCurrentPoint) {
			resetExitTimer();
			const fmi2Status status = FMI2DoStep(m_instance, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2CancelStep", [this]() {
			resetExitTimer();
			const fmi2Status status = FMI2CancelStep(m_instance);
			return createReturnValue(status);
		});

		/* Inquire slave status */
		srv.bind("fmi2GetStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			const fmi2Status status = FMI2GetStatus(m_instance, fmi2StatusKind(s), reinterpret_cast<fmi2Status *>(value.data()));
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetRealStatus", [this](int s) {
			resetExitTimer();
			vector<double> value(1);
			const fmi2Status status = FMI2GetRealStatus(m_instance, fmi2StatusKind(s), value.data());
			return createRealReturnValue(status, value);
		});

		srv.bind("fmi2GetIntegerStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			const fmi2Status status = FMI2GetIntegerStatus(m_instance, fmi2StatusKind(s), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetBooleanStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			const fmi2Status status = FMI2GetBooleanStatus(m_instance, fmi2StatusKind(s), value.data());
			return createIntegerReturnValue(status, value);
		});

		//fmi2GetStringStatusTYPE  *m_fmi2GetStringStatus;

	}

};


int main(int argc, char *argv[]) {

	if (argc < 2) {
        cerr << "Usage: server <shared_library> [<lockfile>]" << endl;
		return EXIT_FAILURE;
	}

    try {

        cout << "Loading " << argv[1] << endl;

        FMU fmu(argv[1]);

        s_server = &fmu.srv;
        time(&s_lastActive);


        if (argc > 2) {

            lockFile = argv[2];

#ifdef _WIN32
            DWORD dwThreadIdArray;

            HANDLE hThreadArray = CreateThread(
                NULL,                   // default security attributes
                0,                      // use default stack size  
                checkLockFile,          // thread function name
                NULL,                   // argument to thread function 
                0,                      // use default creation flags 
                &dwThreadIdArray);      // returns the thread identifier
#else
            pthread_t tid;
            
            int err = pthread_create(&tid, NULL, &checkLockFile, NULL);
            
            if (err != 0) {
                printf("Can't create thread :[%s]", strerror(err));
            } else {
                printf("Thread created successfully\n");
            }
#endif
        }

        cout << "Starting RPC server" << endl;

	    fmu.srv.run();

    } catch (const std::exception& e) {
        cerr << e.what() << endl;
        return EXIT_FAILURE;
    }

	return EXIT_SUCCESS;
}
