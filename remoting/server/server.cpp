#include "rpc/server.h"
#include <Windows.h>
#include "Shlwapi.h"
#include <time.h>
#include <list>
#include <iostream>
#include "remoting.h"

extern "C" {
#include "fmi2Functions.h"
}

using namespace std;

#define NOT_IMPLEMENTED return static_cast<int>(fmi2Error);

static list<LogMessage> s_logMessages;

static rpc::server *s_server = nullptr;

time_t s_lastActive;


void logger(fmi2ComponentEnvironment componentEnvironment, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {
	s_logMessages.push_back({instanceName, status, category, message});
}

void* allocateMemory(size_t nobj, size_t size) {
	return calloc(nobj, size);
}

void freeMemory(void* obj) {
	free(obj);
}

static void resetExitTimer() {
	time(&s_lastActive);
}


DWORD WINAPI MyThreadFunction(LPVOID lpParam) {

	while (s_server) {

		time_t currentTime;
		time(&currentTime);

		if (difftime(currentTime, s_lastActive) > 100) {
			cout << "Client inactive for more than 10 seconds. Exiting." << endl;
			s_server->stop();
			return 0;
		}

		Sleep(500);
	}

	return 0;
}

class FMU {

private:

	HMODULE libraryHandle;

	template<typename T> T *get(const char *functionName) {

# ifdef _WIN32
		auto *fp = GetProcAddress(libraryHandle, functionName);
# else
		auto *fp = dlsym(m_libraryHandle, functionName);
# endif

		return reinterpret_cast<T *>(fp);
	}

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

	fmi2CallbackFunctions m_callbacks;
	fmi2Component         m_instance;

	FMU(const string &libraryPath) : srv(rpc::constants::DEFAULT_PORT) {

		/* set the current directory to binaries/win32 */
		char libraryDir[MAX_PATH];
		strcpy(libraryDir, libraryPath.c_str());
		PathRemoveFileSpec(libraryDir);
		SetCurrentDirectory(libraryDir);

		libraryHandle = LoadLibraryA(libraryPath.c_str());

		m_callbacks.logger = logger;
		m_callbacks.allocateMemory = allocateMemory;
		m_callbacks.freeMemory = freeMemory;
		m_callbacks.stepFinished = NULL;
		m_callbacks.componentEnvironment = NULL;

		/***************************************************
		Types for Common Functions
		****************************************************/

		/* Inquire version numbers of header files and setting logging status */
		m_fmi2GetTypesPlatform = get<fmi2GetTypesPlatformTYPE> ("fmi2GetTypesPlatform");
		m_fmi2GetVersion       = get<fmi2GetVersionTYPE>       ("fmi2GetVersion");
		m_fmi2SetDebugLogging  = get<fmi2SetDebugLoggingTYPE>  ("fmi2SetDebugLogging");

		/* Creation and destruction of FMU instances and setting debug status */
		m_fmi2Instantiate  = get<fmi2InstantiateTYPE>  ("fmi2Instantiate");
		m_fmi2FreeInstance = get<fmi2FreeInstanceTYPE> ("fmi2FreeInstance");

		/* Enter and exit initialization mode, terminate and reset */
		m_fmi2SetupExperiment         = get<fmi2SetupExperimentTYPE>         ("fmi2SetupExperiment");
		m_fmi2EnterInitializationMode = get<fmi2EnterInitializationModeTYPE> ("fmi2EnterInitializationMode");
		m_fmi2ExitInitializationMode  = get<fmi2ExitInitializationModeTYPE>  ("fmi2ExitInitializationMode");
		m_fmi2Terminate               = get<fmi2TerminateTYPE>               ("fmi2Terminate");
		m_fmi2Reset                   = get<fmi2ResetTYPE>                   ("fmi2Reset");

		/* Getting and setting variable values */
		m_fmi2GetReal    = get<fmi2GetRealTYPE>    ("fmi2GetReal");
		m_fmi2GetInteger = get<fmi2GetIntegerTYPE> ("fmi2GetInteger");
		m_fmi2GetBoolean = get<fmi2GetBooleanTYPE> ("fmi2GetBoolean");
		m_fmi2GetString  = get<fmi2GetStringTYPE>  ("fmi2GetString");

		m_fmi2SetReal    = get<fmi2SetRealTYPE>    ("fmi2SetReal");
		m_fmi2SetInteger = get<fmi2SetIntegerTYPE> ("fmi2SetInteger");
		m_fmi2SetBoolean = get<fmi2SetBooleanTYPE> ("fmi2SetBoolean");
		m_fmi2SetString  = get<fmi2SetStringTYPE>  ("fmi2SetString");

		/* Getting and setting the internal FMU state */
		m_fmi2GetFMUstate            = get<fmi2GetFMUstateTYPE>            ("fmi2GetFMUstate");
		m_fmi2SetFMUstate            = get<fmi2SetFMUstateTYPE>            ("fmi2SetFMUstate");
		m_fmi2FreeFMUstate           = get<fmi2FreeFMUstateTYPE>           ("fmi2FreeFMUstate");
		m_fmi2SerializedFMUstateSize = get<fmi2SerializedFMUstateSizeTYPE> ("fmi2SerializedFMUstateSize");
		m_fmi2SerializeFMUstate      = get<fmi2SerializeFMUstateTYPE>      ("fmi2SerializeFMUstate");
		m_fmi2DeSerializeFMUstate    = get<fmi2DeSerializeFMUstateTYPE>    ("fmi2DeSerializeFMUstate");

		/* Getting partial derivatives */
		m_fmi2GetDirectionalDerivative = get<fmi2GetDirectionalDerivativeTYPE>("fmi2GetDirectionalDerivative");

		/***************************************************
		Types for Functions for FMI2 for Model Exchange
		****************************************************/

		/* Enter and exit the different modes */
		m_fmi2EnterEventMode                = get<fmi2EnterEventModeTYPE>                ("fmi2EnterEventMode");
		m_fmi2NewDiscreteStates             = get<fmi2NewDiscreteStatesTYPE>             ("fmi2NewDiscreteStates");
		m_fmi2EnterContinuousTimeMode       = get<fmi2EnterContinuousTimeModeTYPE>       ("fmi2EnterContinuousTimeMode");
		m_fmi2CompletedIntegratorStep       = get<fmi2CompletedIntegratorStepTYPE>       ("fmi2CompletedIntegratorStep");

		/* Providing independent variables and re-initialization of caching */
		m_fmi2SetTime                       = get<fmi2SetTimeTYPE>                       ("fmi2SetTime");
		m_fmi2SetContinuousStates           = get<fmi2SetContinuousStatesTYPE>           ("fmi2SetContinuousStates");

		/* Evaluation of the model equations */
		m_fmi2GetDerivatives                = get<fmi2GetDerivativesTYPE>                ("fmi2GetDerivatives");
		m_fmi2GetEventIndicators            = get<fmi2GetEventIndicatorsTYPE>            ("fmi2GetEventIndicators");
		m_fmi2GetContinuousStates           = get<fmi2GetContinuousStatesTYPE>           ("fmi2GetContinuousStates");
		m_fmi2GetNominalsOfContinuousStates = get<fmi2GetNominalsOfContinuousStatesTYPE> ("fmi2GetNominalsOfContinuousStates");

		/***************************************************
		Types for Functions for FMI2 for Co-Simulation
		****************************************************/

		/* Simulating the slave */
		m_fmi2SetRealInputDerivatives  = get<fmi2SetRealInputDerivativesTYPE>  ("fmi2SetRealInputDerivatives");
		m_fmi2GetRealOutputDerivatives = get<fmi2GetRealOutputDerivativesTYPE> ("fmi2GetRealOutputDerivatives");
		m_fmi2DoStep                   = get<fmi2DoStepTYPE>                   ("fmi2DoStep");
		m_fmi2CancelStep               = get<fmi2CancelStepTYPE>               ("fmi2CancelStep");

		/* Inquire slave status */
		m_fmi2GetStatus        = get<fmi2GetStatusTYPE>        ("fmi2GetStatus");
		m_fmi2GetRealStatus    = get<fmi2GetRealStatusTYPE>    ("fmi2GetRealStatus");
		m_fmi2GetIntegerStatus = get<fmi2GetIntegerStatusTYPE> ("fmi2GetIntegerStatus");
		m_fmi2GetBooleanStatus = get<fmi2GetBooleanStatusTYPE> ("fmi2GetBooleanStatus");
		m_fmi2GetStringStatus  = get<fmi2GetStringStatusTYPE>  ("fmi2GetStringStatus");
		
		srv.bind("echo", [](string const& s) {
			return s;
		});

		/* Inquire version numbers of header files and setting logging status */
		srv.bind("fmi2GetTypesPlatform", [this]() { 
			//pixel p;
			//p.status = fmi2OK;
			//p.messages = { "OK!", "so far" };
			//return p;
			//ReturnValue r = { fmi2OK, {{"bb", 0, "foo", "bar"}} };
			s_logMessages.push_back({ "bounce", 0, "fo!", "bar!!" });
			ReturnValue r = { fmi2OK, s_logMessages };
			return r;
			//return m_fmi2GetTypesPlatform();
		});

		srv.bind("fmi2GetVersion",       [this]() { return m_fmi2GetVersion(); });
		srv.bind("fmi2SetDebugLogging",  [this]() { NOT_IMPLEMENTED });

		/* Creation and destruction of FMU instances and setting debug status */
		srv.bind("fmi2Instantiate",      [this](string const& instanceName, int fmuType, string const& fmuGUID, string const& fmuResourceLocation, int visible, int loggingOn) {
			resetExitTimer();
			m_instance = m_fmi2Instantiate(instanceName.c_str(), static_cast<fmi2Type>(fmuType), fmuGUID.c_str(), fmuResourceLocation.c_str(), &m_callbacks, visible, loggingOn);
			return createReturnValue(reinterpret_cast<int>(m_instance));
		});

		srv.bind("fmi2FreeInstance", [this]() { 
			resetExitTimer();
			m_fmi2FreeInstance(m_instance);
		});

		/* Enter and exit initialization mode, terminate and reset */
		srv.bind("fmi2SetupExperiment", [this](int toleranceDefined, double tolerance, double startTime, int stopTimeDefined, double stopTime) {
			resetExitTimer();
			int status = m_fmi2SetupExperiment(m_instance, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2EnterInitializationMode", [this]() {
			resetExitTimer();
			int status = m_fmi2EnterInitializationMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2ExitInitializationMode",  [this]() {
			resetExitTimer();
			int status = m_fmi2ExitInitializationMode(m_instance);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2Terminate", [this]() {
			resetExitTimer();
			int status = m_fmi2Terminate(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2Reset", [this]() {
			resetExitTimer();
			int status = m_fmi2Reset(m_instance);
			return createReturnValue(status);
		});

		/* Getting and setting variable values */
		srv.bind("fmi2GetReal", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<double> value(vr.size());
			int status = m_fmi2GetReal(m_instance, vr.data(), vr.size(), value.data());
			return createRealReturnValue(status, value);
		});

		srv.bind("fmi2GetInteger", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<int> value(vr.size());
			int status = m_fmi2GetInteger(m_instance, vr.data(), vr.size(), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetBoolean", [this](const vector<unsigned int> &vr) {
			resetExitTimer();
			vector<int> value(vr.size());
			int status = m_fmi2GetBoolean(m_instance, vr.data(), vr.size(), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2SetReal", [this](const vector<unsigned int> &vr, const vector<double> &value) {
			resetExitTimer();
			int status = m_fmi2SetReal(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2SetInteger", [this](const vector<unsigned int> &vr, const vector<int> &value) {
			resetExitTimer();
			int status = m_fmi2SetInteger(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2SetBoolean", [this](const vector<unsigned int> &vr, const vector<int> &value) {
			resetExitTimer();
			int status = m_fmi2SetBoolean(m_instance, vr.data(), vr.size(), value.data());
			return createReturnValue(status);
		});

		/* Getting and setting the internal FMU state */
		//fmi2GetFMUstateTYPE *m_fmi2Component c, fmi2FMUstate* FMUstate);
		//fmi2SetFMUstateTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate);
		//fmi2FreeFMUstateTYPE *m_fmi2Component c, fmi2FMUstate* FMUstate);
		//fmi2SerializedFMUstateSizeTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate, size_t* size);
		//fmi2SerializeFMUstateTYPE *m_fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte[], size_t size);
		//fmi2DeSerializeFMUstateTYPE *m_fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate);

		srv.bind("fmi2GetDirectionalDerivative", [this](const vector<unsigned int> &vUnknown_ref, const vector<unsigned int> &vKnown_ref, const vector<double> &dvKnown) {
			resetExitTimer();
			vector<double> dvUnknown(vKnown_ref.size());
			int status = m_fmi2GetDirectionalDerivative(m_instance, vUnknown_ref.data(), vUnknown_ref.size(),
				vKnown_ref.data(), vKnown_ref.size(), dvKnown.data(), dvUnknown.data());
			return createRealReturnValue(status, dvUnknown);
		});

		/***************************************************
		Types for Functions for FMI2 for Model Exchange
		****************************************************/

		/* Enter and exit the different modes */
		srv.bind("fmi2EnterEventMode", [this]() {
			resetExitTimer();
			int status = m_fmi2EnterEventMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2NewDiscreteStates", [this]() {
			resetExitTimer();
			fmi2EventInfo eventInfo = { 0 };
			int status = m_fmi2NewDiscreteStates(m_instance, &eventInfo);
			return createEventInfoReturnValue(status, &eventInfo);
		});

		srv.bind("fmi2EnterContinuousTimeMode", [this]() {
			resetExitTimer();
			int status = m_fmi2EnterContinuousTimeMode(m_instance);
			return createReturnValue(status);
		});

		srv.bind("fmi2CompletedIntegratorStep", [this](int noSetFMUStatePriorToCurrentPoint) {
			resetExitTimer();
			vector<int> value(2);
			fmi2Boolean* enterEventMode = &(value.data()[0]);
			fmi2Boolean* terminateSimulation = &(value.data()[1]);
			int status = m_fmi2CompletedIntegratorStep(m_instance, noSetFMUStatePriorToCurrentPoint, enterEventMode, terminateSimulation);
			return createIntegerReturnValue(status, value);
		});

		/* Providing independent variables and re-initialization of caching */
		srv.bind("fmi2SetTime", [this](double time) {
			resetExitTimer();
			int status = m_fmi2SetTime(m_instance, time);
			return createReturnValue(status);
		});

		srv.bind("fmi2SetContinuousStates", [this](const vector<double> &x) {
			resetExitTimer();
			int status = m_fmi2SetContinuousStates(m_instance, x.data(), x.size());
			return createReturnValue(status);
		});

		/* Evaluation of the model equations */
		srv.bind("fmi2GetDerivatives", [this](size_t nx) {
			resetExitTimer();
			vector<double> derivatives(nx);
			int status = m_fmi2GetDerivatives(m_instance, derivatives.data(), nx);
			return createRealReturnValue(status, derivatives);
		});
		
		srv.bind("fmi2GetEventIndicators", [this](size_t ni) {
			resetExitTimer();
			vector<double> eventIndicators(ni);
			int status = m_fmi2GetEventIndicators(m_instance, eventIndicators.data(), ni);
			return createRealReturnValue(status, eventIndicators);
		});

		srv.bind("fmi2GetContinuousStates", [this](size_t nx) {
			resetExitTimer();
			vector<double> x(nx);
			int status = m_fmi2GetContinuousStates(m_instance, x.data(), nx);
			return createRealReturnValue(status, x);
		});

		srv.bind("fmi2GetNominalsOfContinuousStates", [this](size_t nx) {
			resetExitTimer();
			vector<double> x_nominal(nx);
			int status = m_fmi2GetNominalsOfContinuousStates(m_instance, x_nominal.data(), nx);
			return createRealReturnValue(status, x_nominal);
		});

		/***************************************************
		Types for Functions for FMI2 for Co-Simulation
		****************************************************/

		/* Simulating the slave */
		srv.bind("fmi2SetRealInputDerivatives", [this](const vector<unsigned int> &vr, const vector<int> &order, const vector<double> &value) {
			resetExitTimer();
			int status = m_fmi2SetRealInputDerivatives(m_instance, vr.data(), vr.size(), order.data(), value.data());
			return createReturnValue(status);
		});

		srv.bind("fmi2GetRealOutputDerivatives", [this](const vector<unsigned int> &vr, const vector<int> &order) {
			resetExitTimer();
			vector<double> value(vr.size());
			int status = m_fmi2GetRealOutputDerivatives(m_instance, vr.data(), vr.size(), order.data(), value.data());
			return createRealReturnValue(status, value);
		});

		srv.bind("fmi2DoStep", [this](double currentCommunicationPoint, double communicationStepSize, int noSetFMUStatePriorToCurrentPoint) {
			resetExitTimer();
			int status = m_fmi2DoStep(m_instance, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint);
			return createReturnValue(status);
		});
		
		srv.bind("fmi2CancelStep", [this]() {
			resetExitTimer();
			int status = m_fmi2CancelStep(m_instance);
			return createReturnValue(status);
		});

		/* Inquire slave status */
		srv.bind("fmi2GetStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			int status = m_fmi2GetStatus(m_instance, fmi2StatusKind(s), reinterpret_cast<fmi2Status *>(value.data()));
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetRealStatus", [this](int s) {
			resetExitTimer();
			vector<double> value(1);
			int status = m_fmi2GetRealStatus(m_instance, fmi2StatusKind(s), value.data());
			return createRealReturnValue(status, value);
		});

		srv.bind("fmi2GetIntegerStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			int status = m_fmi2GetIntegerStatus(m_instance, fmi2StatusKind(s), value.data());
			return createIntegerReturnValue(status, value);
		});

		srv.bind("fmi2GetBooleanStatus", [this](int s) {
			resetExitTimer();
			vector<int> value(1);
			int status = m_fmi2GetBooleanStatus(m_instance, fmi2StatusKind(s), value.data());
			return createIntegerReturnValue(status, value);
		});

		//fmi2GetStringStatusTYPE  *m_fmi2GetStringStatus;

	}

	/***************************************************
	Types for Common Functions
	****************************************************/

	/* Inquire version numbers of header files and setting logging status */
	fmi2GetTypesPlatformTYPE *m_fmi2GetTypesPlatform;
	fmi2GetVersionTYPE       *m_fmi2GetVersion;
	fmi2SetDebugLoggingTYPE  *m_fmi2SetDebugLogging;

	/* Creation and destruction of FMU instances and setting debug status */
	fmi2InstantiateTYPE  *m_fmi2Instantiate;
	fmi2FreeInstanceTYPE *m_fmi2FreeInstance;

	/* Enter and exit initialization mode, terminate and reset */
	fmi2SetupExperimentTYPE         *m_fmi2SetupExperiment;
	fmi2EnterInitializationModeTYPE *m_fmi2EnterInitializationMode;
	fmi2ExitInitializationModeTYPE  *m_fmi2ExitInitializationMode;
	fmi2TerminateTYPE               *m_fmi2Terminate;
	fmi2ResetTYPE                   *m_fmi2Reset;

	/* Getting and setting variable values */
	fmi2GetRealTYPE    *m_fmi2GetReal;
	fmi2GetIntegerTYPE *m_fmi2GetInteger;
	fmi2GetBooleanTYPE *m_fmi2GetBoolean;
	fmi2GetStringTYPE  *m_fmi2GetString;

	fmi2SetRealTYPE    *m_fmi2SetReal;
	fmi2SetIntegerTYPE *m_fmi2SetInteger;
	fmi2SetBooleanTYPE *m_fmi2SetBoolean;
	fmi2SetStringTYPE  *m_fmi2SetString;

	/* Getting and setting the internal FMU state */
	fmi2GetFMUstateTYPE            *m_fmi2GetFMUstate;
	fmi2SetFMUstateTYPE            *m_fmi2SetFMUstate;
	fmi2FreeFMUstateTYPE           *m_fmi2FreeFMUstate;
	fmi2SerializedFMUstateSizeTYPE *m_fmi2SerializedFMUstateSize;
	fmi2SerializeFMUstateTYPE      *m_fmi2SerializeFMUstate;
	fmi2DeSerializeFMUstateTYPE    *m_fmi2DeSerializeFMUstate;

	/* Getting partial derivatives */
	fmi2GetDirectionalDerivativeTYPE *m_fmi2GetDirectionalDerivative;

	/***************************************************
	Types for Functions for FMI2 for Model Exchange
	****************************************************/

	/* Enter and exit the different modes */
	fmi2EnterEventModeTYPE          *m_fmi2EnterEventMode;
	fmi2NewDiscreteStatesTYPE       *m_fmi2NewDiscreteStates;
	fmi2EnterContinuousTimeModeTYPE *m_fmi2EnterContinuousTimeMode;
	fmi2CompletedIntegratorStepTYPE *m_fmi2CompletedIntegratorStep;

	/* Providing independent variables and re-initialization of caching */
	fmi2SetTimeTYPE             *m_fmi2SetTime;
	fmi2SetContinuousStatesTYPE *m_fmi2SetContinuousStates;

	/* Evaluation of the model equations */
	fmi2GetDerivativesTYPE                *m_fmi2GetDerivatives;
	fmi2GetEventIndicatorsTYPE            *m_fmi2GetEventIndicators;
	fmi2GetContinuousStatesTYPE           *m_fmi2GetContinuousStates;
	fmi2GetNominalsOfContinuousStatesTYPE *m_fmi2GetNominalsOfContinuousStates;

	/***************************************************
	Types for Functions for FMI2 for Co-Simulation
	****************************************************/

	/* Simulating the slave */
	fmi2SetRealInputDerivativesTYPE  *m_fmi2SetRealInputDerivatives;
	fmi2GetRealOutputDerivativesTYPE *m_fmi2GetRealOutputDerivatives;
	fmi2DoStepTYPE                   *m_fmi2DoStep;
	fmi2CancelStepTYPE               *m_fmi2CancelStep;

	/* Inquire slave status */
	fmi2GetStatusTYPE        *m_fmi2GetStatus;
	fmi2GetRealStatusTYPE    *m_fmi2GetRealStatus;
	fmi2GetIntegerStatusTYPE *m_fmi2GetIntegerStatus;
	fmi2GetBooleanStatusTYPE *m_fmi2GetBooleanStatus;
	fmi2GetStringStatusTYPE  *m_fmi2GetStringStatus;

};


int main(int argc, char *argv[]) {

	if (argc != 2) {
		return EXIT_FAILURE;
	}

	FMU fmu(argv[1]);

	s_server = &fmu.srv;
	time(&s_lastActive);

	DWORD dwThreadIdArray;

	auto hThreadArray = CreateThread(
		NULL,                   // default security attributes
		0,                      // use default stack size  
		MyThreadFunction,       // thread function name
		NULL,                   // argument to thread function 
		0,                      // use default creation flags 
		&dwThreadIdArray);      // returns the thread identifier

	fmu.srv.run();

	return EXIT_SUCCESS;
}
