#include <iostream>
#include <Windows.h>

extern "C" {
#include "fmi2Functions.h"
}

using namespace std;

template<typename T> T *get(HMODULE libraryHandle, const char *functionName) {

# ifdef _WIN32
	auto *fp = GetProcAddress(libraryHandle, functionName);
# else
	auto *fp = dlsym(m_libraryHandle, functionName);
# endif

	return reinterpret_cast<T *>(fp);
}

static void functionInThisDll() {}

void logger(fmi2ComponentEnvironment componentEnvironment, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {
	puts(message);
}


int main()
{
	// load the shared library
# ifdef _WIN32
	auto l = LoadLibraryA("client.dll");
# else
	auto l = dlopen("client.so", RTLD_LAZY);
# endif

	auto getTypesPlatform        = get<fmi2GetVersionTYPE>              (l, "fmi2GetTypesPlatform");
	auto getVersion              = get<fmi2GetVersionTYPE>              (l, "fmi2GetVersion");
	auto instantiate             = get<fmi2InstantiateTYPE>             (l, "fmi2Instantiate");
	auto setupExperiment         = get<fmi2SetupExperimentTYPE>         (l, "fmi2SetupExperiment");
	auto enterInitializationMode = get<fmi2EnterInitializationModeTYPE> (l, "fmi2EnterInitializationMode");
	auto exitInitializationMode  = get<fmi2ExitInitializationModeTYPE>  (l, "fmi2ExitInitializationMode");
	auto getReal                 = get<fmi2GetRealTYPE>                 (l, "fmi2GetReal");
	auto doStep                  = get<fmi2DoStepTYPE>                  (l, "fmi2DoStep");
	auto terminate               = get<fmi2TerminateTYPE>               (l, "fmi2Terminate");
	auto freeInstance            = get<fmi2FreeInstanceTYPE>            (l, "fmi2FreeInstance");

	auto typesPlatform = getTypesPlatform();
	auto version = getVersion();
	fmi2CallbackFunctions functions = { logger,	nullptr, nullptr, nullptr, nullptr };
	
	auto c = instantiate("bb", fmi2CoSimulation, "{8c4e810f-3df3-4a00-8276-176fa3c9f003}", "", &functions, fmi2False, fmi2False);

	fmi2Status status = fmi2OK;

	const fmi2Real stopTime = 3;
	const fmi2Real stepSize = 0.1;

	status = setupExperiment(c, fmi2False, 0, 0, fmi2True, stopTime);

	status = enterInitializationMode(c);
	status = exitInitializationMode(c);

	fmi2ValueReference vr[2] = { 0, 1 };
	fmi2Real value[2] = { 0, 0 };

	fmi2Real time = 0;

	while (time <= stopTime) {
		status = getReal(c, vr, 2, value);
		cout << time << ", " << value[0] << ", " << value[1] << endl;
		status = doStep(c, time, stepSize, fmi2True);
		time += stepSize;
	}

	status = terminate(c);
	
	freeInstance(c);

	cout << "FMI Version: " << version << endl;

	auto b = FreeLibrary(l);
	


	return 0;
}