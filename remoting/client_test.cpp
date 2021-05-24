#ifdef _WIN32
#include <Windows.h>
#else
#include <dlfcn.h>
#endif

#include <iostream>

#include "fmi2Functions.h"


using namespace std;

#ifdef _WIN32
template<typename T> T *get(HMODULE libraryHandle, const char *functionName) {
    void *fp = GetProcAddress(libraryHandle, functionName);
	return reinterpret_cast<T *>(fp);
}
#else
template<typename T> T *get(void *libraryHandle, const char *functionName) {
    void *fp = dlsym(libraryHandle, functionName);
    cout << functionName << " = " << fp << endl;
    return reinterpret_cast<T *>(fp);
}
# endif

static void functionInThisDll() {}

void logger(fmi2ComponentEnvironment componentEnvironment, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {
    cout << message << endl;
}


int main()
{
	// load the shared library
# ifdef _WIN32
	auto l = LoadLibraryA("client.dll");
# else
	auto l = dlopen("/mnt/e/Development/FMPy/remoting/linux64/client.so", RTLD_LAZY);
# endif

    cout << l << endl;


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

    cout << typesPlatform << endl;

	auto version = getVersion();

    cout << version << endl;

    fmi2CallbackFunctions functions = { logger,	nullptr, nullptr, nullptr, nullptr };

	auto c = instantiate("bb", fmi2CoSimulation, "{8c4e810f-3df3-4a00-8276-176fa3c9f003}", "", &functions, fmi2False, fmi2False);

    cout << c << endl;

    //return 0;

	fmi2Status status = fmi2OK;

	const fmi2Real stopTime = 3;
	const fmi2Real stepSize = 0.1;

	status = setupExperiment(c, fmi2False, 0, 0, fmi2True, stopTime);

	status = enterInitializationMode(c);
	status = exitInitializationMode(c);

	fmi2ValueReference vr[2] = { 1, 3 };
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

#ifdef _WIN32
	auto b = FreeLibrary(l);
#else
    auto b = dlclose(l);
#endif

	return 0;
}