/* This file is part of FMPy. See LICENSE.txt for license information. */

#if defined(_WIN32)
#include <Windows.h>
#include <shlwapi.h>
#pragma comment(lib, "shlwapi.lib")
#elif defined(__APPLE__)
#include <libgen.h>
#include <dlfcn.h>
#include <sys/syslimits.h>
#else
#define _GNU_SOURCE
#include <libgen.h>
#include <dlfcn.h>
#include <linux/limits.h>
#endif

#include <mpack.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#include "fmi2Functions.h"


typedef struct {

#if defined(_WIN32)
    HMODULE libraryHandle;
#else
    void *libraryHandle;
#endif

    fmi2Component c;
	fmi2CallbackLogger logger;

    /***************************************************
    Common Functions
    ****************************************************/
    fmi2GetTypesPlatformTYPE         *fmi2GetTypesPlatform;
    fmi2GetVersionTYPE               *fmi2GetVersion;
    fmi2SetDebugLoggingTYPE          *fmi2SetDebugLogging;
    fmi2InstantiateTYPE              *fmi2Instantiate;
    fmi2FreeInstanceTYPE             *fmi2FreeInstance;
    fmi2SetupExperimentTYPE          *fmi2SetupExperiment;
    fmi2EnterInitializationModeTYPE  *fmi2EnterInitializationMode;
    fmi2ExitInitializationModeTYPE   *fmi2ExitInitializationMode;
    fmi2TerminateTYPE                *fmi2Terminate;
    fmi2ResetTYPE                    *fmi2Reset;
    fmi2GetRealTYPE                  *fmi2GetReal;
    fmi2GetIntegerTYPE               *fmi2GetInteger;
    fmi2GetBooleanTYPE               *fmi2GetBoolean;
    fmi2GetStringTYPE                *fmi2GetString;
    fmi2SetRealTYPE                  *fmi2SetReal;
    fmi2SetIntegerTYPE               *fmi2SetInteger;
    fmi2SetBooleanTYPE               *fmi2SetBoolean;
    fmi2SetStringTYPE                *fmi2SetString;
    fmi2GetFMUstateTYPE              *fmi2GetFMUstate;
    fmi2SetFMUstateTYPE              *fmi2SetFMUstate;
    fmi2FreeFMUstateTYPE             *fmi2FreeFMUstate;
    fmi2SerializedFMUstateSizeTYPE   *fmi2SerializedFMUstateSize;
    fmi2SerializeFMUstateTYPE        *fmi2SerializeFMUstate;
    fmi2DeSerializeFMUstateTYPE      *fmi2DeSerializeFMUstate;
    fmi2GetDirectionalDerivativeTYPE *fmi2GetDirectionalDerivative;

	/***************************************************
	Functions for FMI2 for Co-Simulation
	****************************************************/

	/* Simulating the slave */
	fmi2SetRealInputDerivativesTYPE  *fmi2SetRealInputDerivatives;
	fmi2GetRealOutputDerivativesTYPE *fmi2GetRealOutputDerivatives;

	fmi2DoStepTYPE     *fmi2DoStep;
	fmi2CancelStepTYPE *fmi2CancelStep;

	/* Inquire slave status */
	fmi2GetStatusTYPE        *fmi2GetStatus;
	fmi2GetRealStatusTYPE    *fmi2GetRealStatus;
	fmi2GetIntegerStatusTYPE *fmi2GetIntegerStatus;
	fmi2GetBooleanStatusTYPE *fmi2GetBooleanStatus;
	fmi2GetStringStatusTYPE  *fmi2GetStringStatus;

	const char *name;
	const char *guid;
	const char *modelIdentifier;

} Model;

typedef struct {

    size_t size;
	size_t *ci;
	fmi2ValueReference *vr;

} VariableMapping;

typedef struct {

	char type;
	size_t startComponent;
	fmi2ValueReference startValueReference;
	size_t endComponent;
	fmi2ValueReference endValueReference;

} Connection;

typedef struct {

	size_t nComponents;
	Model *components;
	
	size_t nVariables;
	VariableMapping *variables;

	size_t nConnections;
	Connection *connections;

} System;


#define GET_SYSTEM \
	if (!c) return fmi2Error; \
	System *s = (System *)c; \
	fmi2Status status = fmi2OK;

#define CHECK_STATUS(S) status = S; if (status > fmi2Warning) goto END;


/***************************************************
Types for Common Functions
****************************************************/

/* Inquire version numbers of header files and setting logging status */
const char* fmi2GetTypesPlatform(void) { return fmi2TypesPlatform; }

const char* fmi2GetVersion(void) { return fmi2Version; }

fmi2Status fmi2SetDebugLogging(fmi2Component c, fmi2Boolean loggingOn, size_t nCategories, const fmi2String categories[]) {
    
	GET_SYSTEM

		for (size_t i = 0; i < s->nComponents; i++) {
			Model *m = &(s->components[i]);
			CHECK_STATUS(m->fmi2SetDebugLogging(m->c, loggingOn, nCategories, categories))
		}

END:
	return status;
}


/* Creation and destruction of FMU instances and setting debug status */
#ifdef _WIN32
#define GET(f) m->f = (f ## TYPE *)GetProcAddress(m->libraryHandle, #f); if (!m->f) { return NULL; }
#else
#define GET(f) m->f = (f ## TYPE *)dlsym(m->libraryHandle, #f); if (!m->f) { return NULL; }
#endif

/* Creation and destruction of FMU instances and setting debug status */
fmi2Component fmi2Instantiate(fmi2String instanceName,
                              fmi2Type fmuType,
                              fmi2String fmuGUID,
                              fmi2String fmuResourceLocation,
                              const fmi2CallbackFunctions* functions,
                              fmi2Boolean visible,
                              fmi2Boolean loggingOn) {

	if (!functions || !functions->logger) {
		return NULL;
	}

    if (fmuType != fmi2CoSimulation) {
        functions->logger(NULL, instanceName, fmi2Error, "logError", "Argument fmuType must be fmi2CoSimulation.");
        return NULL;
    }

	const char *scheme1 = "file:///";
	const char *scheme2 = "file:/";
	char *path;

	if (strncmp(fmuResourceLocation, scheme1, strlen(scheme1)) == 0) {
		path = strdup(&fmuResourceLocation[strlen(scheme1) - 1]);
	} else if (strncmp(fmuResourceLocation, scheme2, strlen(scheme2)) == 0) {
		path = strdup(&fmuResourceLocation[strlen(scheme2) - 1]);
	} else {
        functions->logger(NULL, instanceName, fmi2Error, "logError", "The fmuResourceLocation must start with \"file:///\" or \"file:/\".");
		return NULL;
	}

#ifdef _WIN32
	// strip leading slash if path starts with a drive letter
    if (strlen(path) > 2 && path[0] == '/' && path[2] == ':') {
		strcpy(path, &path[1]);
	}
#endif

	System *s = calloc(1, sizeof(System));
#ifdef _WIN32
    char configPath[MAX_PATH] = "";
#else
    char configPath[PATH_MAX] = "";
#endif
	strcpy(configPath, path);
	strcat(configPath, "/config.mp");

	// parse a file into a node tree
	mpack_tree_t tree;
	mpack_tree_init_filename(&tree, configPath, 0);
	mpack_tree_parse(&tree);
	mpack_node_t root = mpack_tree_root(&tree);

	//mpack_node_print_to_stdout(root);

	mpack_node_t components = mpack_node_map_cstr(root, "components");

	s->nComponents = mpack_node_array_length(components);

	s->components = calloc(s->nComponents, sizeof(Model));

	for (size_t i = 0; i < s->nComponents; i++) {
		mpack_node_t component = mpack_node_array_at(components, i);

		mpack_node_t name = mpack_node_map_cstr(component, "name");
		s->components[i].name = mpack_node_cstr_alloc(name, 1024);

		mpack_node_t guid = mpack_node_map_cstr(component, "guid");
		s->components[i].guid = mpack_node_cstr_alloc(guid, 1024);

		mpack_node_t modelIdentifier = mpack_node_map_cstr(component, "modelIdentifier");
		s->components[i].modelIdentifier = mpack_node_cstr_alloc(modelIdentifier, 1024);
	}

	mpack_node_t connections = mpack_node_map_cstr(root, "connections");

	s->nConnections = mpack_node_array_length(connections);

	s->connections = calloc(s->nConnections, sizeof(Connection));

	for (size_t i = 0; i < s->nConnections; i++) {
		mpack_node_t connection = mpack_node_array_at(connections, i);

		mpack_node_t type = mpack_node_map_cstr(connection, "type");
		s->connections[i].type = mpack_node_str(type)[0];

		mpack_node_t startComponent = mpack_node_map_cstr(connection, "startComponent");
		s->connections[i].startComponent = mpack_node_u64(startComponent);

		mpack_node_t endComponent = mpack_node_map_cstr(connection, "endComponent");
		s->connections[i].endComponent = mpack_node_u64(endComponent);

		mpack_node_t startValueReference = mpack_node_map_cstr(connection, "startValueReference");
		s->connections[i].startValueReference = mpack_node_u32(startValueReference);

		mpack_node_t endValueReference = mpack_node_map_cstr(connection, "endValueReference");
		s->connections[i].endValueReference = mpack_node_u32(endValueReference);
	}

	mpack_node_t variables = mpack_node_map_cstr(root, "variables");

	s->nVariables = mpack_node_array_length(variables);

	s->variables = calloc(s->nVariables, sizeof(VariableMapping));

	for (size_t i = 0; i < s->nVariables; i++) {
		
        mpack_node_t variable = mpack_node_array_at(variables, i);

        mpack_node_t components = mpack_node_map_cstr(variable, "components");
        mpack_node_t valueReferences = mpack_node_map_cstr(variable, "valueReferences");

        s->variables[i].size = mpack_node_array_length(components);
        s->variables[i].ci = calloc(s->variables[i].size, sizeof(size_t));
        s->variables[i].vr = calloc(s->variables[i].size, sizeof(fmi2ValueReference));

        for (size_t j = 0; j < s->variables[i].size; j++) {

            mpack_node_t component = mpack_node_array_at(components, j);
            mpack_node_t valueReference = mpack_node_array_at(valueReferences, j);

            s->variables[i].ci[j] = mpack_node_u64(component);
            s->variables[i].vr[j] = mpack_node_u32(valueReference);
        }
		
	}

	// clean up and check for errors
	if (mpack_tree_destroy(&tree) != mpack_ok) {
        functions->logger(NULL, instanceName, fmi2Error, "logError", "An error occurred decoding %s.", configPath);
		return NULL;
	}

	for (size_t i = 0; i < s->nComponents; i++) {

		Model *m = &(s->components[i]);

		m->logger = functions->logger;

#ifdef _WIN32
		char libraryPath[MAX_PATH] = "";

		PathCombine(libraryPath, path, m->modelIdentifier);
		PathCombine(libraryPath, libraryPath, "binaries");
#ifdef _WIN64
		PathCombine(libraryPath, libraryPath, "win64");
#else
		PathCombine(libraryPath, libraryPath, "win32");
#endif
		PathCombine(libraryPath, libraryPath, m->modelIdentifier);
		strcat(libraryPath, ".dll");

		m->libraryHandle = LoadLibrary(libraryPath);
#else
        char libraryPath[PATH_MAX] = "";
        strcpy(libraryPath, path);
        strcat(libraryPath, "/");
        strcat(libraryPath, m->modelIdentifier);
#ifdef __APPLE__
        strcat(libraryPath, "/binaries/darwin64/");
        strcat(libraryPath, m->modelIdentifier);
        strcat(libraryPath, ".dylib");
#else
        strcat(libraryPath, "/binaries/linux64/");
        strcat(libraryPath, m->modelIdentifier);
        strcat(libraryPath, ".so");
#endif
        m->libraryHandle = dlopen(libraryPath, RTLD_LAZY);
#endif

#ifdef _WIN32
		char resourcesPath[MAX_PATH];
#else
        char resourcesPath[PATH_MAX];
#endif
		strcpy(resourcesPath, fmuResourceLocation);
		strcat(resourcesPath, "/");
		strcat(resourcesPath, m->modelIdentifier);
		strcat(resourcesPath, "/resources");

		if (!m->libraryHandle) {
			functions->logger(functions->componentEnvironment, instanceName, fmi2Error, "error", "Failed to load shared library %s.", libraryPath);
			return NULL;
		}

		GET(fmi2GetTypesPlatform)
		GET(fmi2GetVersion)
		GET(fmi2SetDebugLogging)
		GET(fmi2Instantiate)
		GET(fmi2FreeInstance)
		GET(fmi2SetupExperiment)
		GET(fmi2EnterInitializationMode)
		GET(fmi2ExitInitializationMode)
		GET(fmi2Terminate)
		GET(fmi2Reset)
		GET(fmi2GetReal)
		GET(fmi2GetInteger)
		GET(fmi2GetBoolean)
		GET(fmi2GetString)
		GET(fmi2SetReal)
		GET(fmi2SetInteger)
		GET(fmi2SetBoolean)
		GET(fmi2SetString)
		GET(fmi2GetFMUstate)
		GET(fmi2SetFMUstate)
		GET(fmi2FreeFMUstate)
		GET(fmi2SerializedFMUstateSize)
		GET(fmi2SerializeFMUstate)
		GET(fmi2DeSerializeFMUstate)
		GET(fmi2GetDirectionalDerivative)

		GET(fmi2SetRealInputDerivatives)
		GET(fmi2GetRealOutputDerivatives)
		GET(fmi2DoStep)
		GET(fmi2CancelStep)
		GET(fmi2GetStatus)
		GET(fmi2GetRealStatus)
		GET(fmi2GetIntegerStatus)
		GET(fmi2GetBooleanStatus)
		GET(fmi2GetStringStatus)

		m->c = m->fmi2Instantiate(m->name, fmi2CoSimulation, m->guid, resourcesPath, functions, visible, loggingOn);

		if (!m->c) return NULL;
	}

    return s;
}

void fmi2FreeInstance(fmi2Component c) {

	if (!c) return;
	
	System *s = (System *)c;

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		m->fmi2FreeInstance(m->c);
#ifdef _WIN32
		FreeLibrary(m->libraryHandle);
#else
		dlclose(m->libraryHandle);
#endif
	}

	free(s);
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status fmi2SetupExperiment(fmi2Component c,
                               fmi2Boolean toleranceDefined,
                               fmi2Real tolerance,
                               fmi2Real startTime,
                               fmi2Boolean stopTimeDefined,
                               fmi2Real stopTime) {
    
	GET_SYSTEM

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		CHECK_STATUS(m->fmi2SetupExperiment(m->c, toleranceDefined, tolerance, startTime, stopTimeDefined, stopTime))
	}

END:
	return status;
}

fmi2Status fmi2EnterInitializationMode(fmi2Component c) {
	
	GET_SYSTEM

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		CHECK_STATUS(m->fmi2EnterInitializationMode(m->c))
	}

END:
	return status;
}

fmi2Status fmi2ExitInitializationMode(fmi2Component c) {
	
	GET_SYSTEM

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		CHECK_STATUS(m->fmi2ExitInitializationMode(m->c))
	}

END:
	return status;
}

fmi2Status fmi2Terminate(fmi2Component c) {
	
	GET_SYSTEM

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		CHECK_STATUS(m->fmi2Terminate(m->c))
	}

END:
	return status;
}

fmi2Status fmi2Reset(fmi2Component c) {

	GET_SYSTEM

		for (size_t i = 0; i < s->nComponents; i++) {
			Model *m = &(s->components[i]);
			CHECK_STATUS(m->fmi2Reset(m->c))
		}

END:
	return status;
}

/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
    
	GET_SYSTEM

	for (size_t i = 0; i < nvr; i++) {
		if (vr[i] >= s->nVariables) return fmi2Error;
		VariableMapping vm = s->variables[vr[i]];
		Model *m = &(s->components[vm.ci[0]]);
		CHECK_STATUS(m->fmi2GetReal(m->c, &(vm.vr[0]), 1, &value[i]))
	}
END:
	return status;
}

fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {

	GET_SYSTEM

		for (size_t i = 0; i < nvr; i++) {
			if (vr[i] >= s->nVariables) return fmi2Error;
			VariableMapping vm = s->variables[vr[i]];
			Model *m = &(s->components[vm.ci[0]]);
			CHECK_STATUS(m->fmi2GetInteger(m->c, &(vm.vr[0]), 1, &value[i]))
		}
END:
	return status;
}

fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {

	GET_SYSTEM

		for (size_t i = 0; i < nvr; i++) {
			if (vr[i] >= s->nVariables) return fmi2Error;
			VariableMapping vm = s->variables[vr[i]];
			Model *m = &(s->components[vm.ci[0]]);
			CHECK_STATUS(m->fmi2GetBoolean(m->c, &(vm.vr[0]), 1, &value[i]))
		}
END:
	return status;
}

fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {

	GET_SYSTEM

		for (size_t i = 0; i < nvr; i++) {
			if (vr[i] >= s->nVariables) return fmi2Error;
			VariableMapping vm = s->variables[vr[i]];
			Model *m = &(s->components[vm.ci[0]]);
			CHECK_STATUS(m->fmi2GetString(m->c, &(vm.vr[0]), 1, &value[i]))
		}
END:
	return status;
}

fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {
	
	GET_SYSTEM

	for (size_t i = 0; i < nvr; i++) {
		if (vr[i] >= s->nVariables) return fmi2Error;
		VariableMapping vm = s->variables[vr[i]];
        for (size_t j = 0; j < vm.size; j++) {
            Model *m = &(s->components[vm.ci[j]]);
		    CHECK_STATUS(m->fmi2SetReal(m->c, &(vm.vr[j]), 1, &value[i]))
        }
	}
END:
	return status;
}

fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {

	GET_SYSTEM

	for (size_t i = 0; i < nvr; i++) {
		if (vr[i] >= s->nVariables) return fmi2Error;
		VariableMapping vm = s->variables[vr[i]];
        for (size_t j = 0; j < vm.size; j++) {
            Model *m = &(s->components[vm.ci[j]]);
            CHECK_STATUS(m->fmi2SetInteger(m->c, &(vm.vr[j]), 1, &value[i]))
        }
	}
END:
	return status;
}

fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {

	GET_SYSTEM

	for (size_t i = 0; i < nvr; i++) {
		if (vr[i] >= s->nVariables) return fmi2Error;
		VariableMapping vm = s->variables[vr[i]];
        for (size_t j = 0; j < vm.size; j++) {
            Model *m = &(s->components[vm.ci[j]]);
            CHECK_STATUS(m->fmi2SetBoolean(m->c, &(vm.vr[j]), 1, &value[i]))
        }
	}
END:
	return status;
}

fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]) {

	GET_SYSTEM

	for (size_t i = 0; i < nvr; i++) {
		if (vr[i] >= s->nVariables) return fmi2Error;
		VariableMapping vm = s->variables[vr[i]];
        for (size_t j = 0; j < vm.size; j++) {
            Model *m = &(s->components[vm.ci[j]]);
            CHECK_STATUS(m->fmi2SetString(m->c, &(vm.vr[j]), 1, &value[i]))
        }
	}
END:
	return status;
}

/* Getting and setting the internal FMU state */
fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    return fmi2Error;
}

fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) {
    return fmi2Error;
}

fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    return fmi2Error;
}

fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t* size) {
    return fmi2Error;
}

fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte serializedState[], size_t size) {
    return fmi2Error;
}

fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
    return fmi2Error;
}

/* Getting partial derivatives */
fmi2Status fmi2GetDirectionalDerivative(fmi2Component c,
                                        const fmi2ValueReference vUnknown_ref[], size_t nUnknown,
                                        const fmi2ValueReference vKnown_ref[],   size_t nKnown,
                                        const fmi2Real dvKnown[],
                                        fmi2Real dvUnknown[]) {
    return fmi2Error;
}

/***************************************************
Types for Functions for FMI2 for Co-Simulation
****************************************************/

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c,
                                       const fmi2ValueReference vr[], size_t nvr,
                                       const fmi2Integer order[],
                                       const fmi2Real value[]) {
    return fmi2Error;
}

fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c,
                                        const fmi2ValueReference vr[], size_t nvr,
                                        const fmi2Integer order[],
                                        fmi2Real value[]) {
    return fmi2Error;
}

fmi2Status fmi2DoStep(fmi2Component c,
                      fmi2Real      currentCommunicationPoint,
                      fmi2Real      communicationStepSize,
                      fmi2Boolean   noSetFMUStatePriorToCurrentPoint) {

	GET_SYSTEM

	for (size_t i = 0; i < s->nConnections; i++) {
		fmi2Real realValue;
		fmi2Integer integerValue;
		fmi2Boolean booleanValue;
		Connection *k = &(s->connections[i]);
		Model *m1 = &(s->components[k->startComponent]);
		Model *m2 = &(s->components[k->endComponent]);
		fmi2ValueReference vr1 = k->startValueReference;
		fmi2ValueReference vr2 = k->endValueReference;

		switch (k->type) {
		case 'R':
			CHECK_STATUS(m1->fmi2GetReal(m1->c, &(vr1), 1, &realValue))
			CHECK_STATUS(m2->fmi2SetReal(m2->c, &(vr2), 1, &realValue))
			break;
		case 'I':
			CHECK_STATUS(m1->fmi2GetInteger(m1->c, &(vr1), 1, &integerValue))
			CHECK_STATUS(m2->fmi2SetInteger(m2->c, &(vr2), 1, &integerValue))
			break;
		case 'B':
			CHECK_STATUS(m1->fmi2GetBoolean(m1->c, &(vr1), 1, &booleanValue))
			CHECK_STATUS(m2->fmi2SetBoolean(m2->c, &(vr2), 1, &booleanValue))
			break;
		}
		
	}

	for (size_t i = 0; i < s->nComponents; i++) {
		Model *m = &(s->components[i]);
		CHECK_STATUS(m->fmi2DoStep(m->c, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint))
	}

END:
	return status;
}

fmi2Status fmi2CancelStep(fmi2Component c) {
    return fmi2Error;
}

/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status*  value) {
    return fmi2Error;
}

fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real*    value) {
    return fmi2Error;
}

fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
    return fmi2Error;
}

fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
    return fmi2Error;
}

fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String*  value) {
    return fmi2Error;
}
