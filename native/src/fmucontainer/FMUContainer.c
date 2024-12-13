/* This file is part of FMPy. See LICENSE.txt for license information. */

#if defined(_WIN32)
#include <shlwapi.h>
#pragma comment(lib, "shlwapi.lib")
#elif defined(__APPLE__)
#include <libgen.h>
#include <sys/syslimits.h>
#else
#define _GNU_SOURCE
#include <libgen.h>
#include <linux/limits.h>
#endif

#include <mpack.h>

#include <string.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>

#include "fmi3FunctionTypes.h"

#include "FMI2.h"

#include "FMUContainer.h"


#define CHECK_STATUS(S) status = S; if (status > FMIWarning) goto END


#ifdef _WIN32
static DWORD WINAPI instanceDoStep(LPVOID lpParam) {

    Component *c = (Component *)lpParam;

    while (true) {

        DWORD dwWaitResult = WaitForSingleObject(c->mutex, INFINITE);

        if (c->terminate) {
            return TRUE;
        }

        if (c->doStep) {
            c->status = FMI2DoStep(c->instance, c->currentCommunicationPoint, c->communicationStepSize, fmi2True);
            c->doStep = false;
        }

        BOOL success = ReleaseMutex(c->mutex);
    }

    return TRUE;
}
#else
static void* instanceDoStep(void *arg) {

    Component *c = (Component *)arg;

    while (true) {

        pthread_mutex_lock(&c->mutex);

        if (c->terminate) {
            return NULL;
        }

        if (c->doStep) {
            c->status = FMI2DoStep(c->instance, c->currentCommunicationPoint, c->communicationStepSize, fmi2True);
            c->doStep = false;
        }

        pthread_mutex_unlock(&c->mutex);
    }

    return NULL;
}
#endif


static void logFMIMessage(FMIInstance *instance, FMIStatus status, const char *category, const char *message) {
    
    if (!instance) {
        return;
    }

    System* s = instance->userData;

    if (!s || !s->logMessage) {
        return;
    }
    
    size_t message_len = strlen(message);
    size_t instanceName_len = strlen(instance->name);
    size_t total_len = message_len + instanceName_len + 5;
    
    char *buf = malloc(total_len);

    snprintf(buf, total_len, "[%s]: %s", instance->name, message);

    switch (s->fmiVersion) {
    case FMIVersion2:
        ((fmi2CallbackLogger)s->logMessage)(s->instanceEnvironment, s->instanceName, status, category, buf);
        break;
    case FMIVersion3:
        ((fmi3LogMessageCallback)s->logMessage)(s->instanceEnvironment, status, category, buf);
        break;
    default:
        break;
    }

    free(buf);
}

static void logFunctionCall(FMIInstance *instance, FMIStatus status, const char *message, ...) {

    if (!instance) {
        return;
    }

    System *s = instance->userData;

    if (!s || !s->logMessage) {
        return;
    }

    char buf[FMI_MAX_MESSAGE_LENGTH] = "";

    const size_t len = snprintf(buf, FMI_MAX_MESSAGE_LENGTH, "[%s] ", instance->name);

    va_list args;

    va_start(args, message);
    vsnprintf(&buf[len], FMI_MAX_MESSAGE_LENGTH - len, message, args);
    va_end(args);

    switch (s->fmiVersion) {
    case FMIVersion2:
        ((fmi2CallbackLogger)s->logMessage)(s->instanceEnvironment, s->instanceName, status, "logDebug", buf);
        break;
    case FMIVersion3:
        ((fmi3LogMessageCallback)s->logMessage)(s->instanceEnvironment, status, "logDebug", buf);
        break;
    default:
        break;
    }
}

System* instantiateSystem(
    FMIVersion fmiVersion,
    const char* resourcesDir,
    const char* instanceName,
    void* logMessage,
    void* instanceEnvironment,
    bool loggingOn,
    bool visible) {

    char configFilename[4096] = "";
    strcpy(configFilename, resourcesDir);
    strcat(configFilename, "config.mp");

    // parse a file into a node tree
    mpack_tree_t tree;
    mpack_tree_init_filename(&tree, configFilename, 0);
    mpack_tree_parse(&tree);
    mpack_node_t root = mpack_tree_root(&tree);

#ifdef _DEBUG
    mpack_node_print_to_stdout(root);
#endif

    mpack_node_t parallelDoStep = mpack_node_map_cstr(root, "parallelDoStep");

    System* s = calloc(1, sizeof(System));

    s->fmiVersion = fmiVersion;
    s->instanceName = strdup(instanceName);
    s->instanceEnvironment = instanceEnvironment;
    s->logMessage = logMessage;
    s->parallelDoStep = mpack_node_bool(parallelDoStep);
    s->time = 0;

    mpack_node_t components = mpack_node_map_cstr(root, "components");

    s->nComponents = mpack_node_array_length(components);

    s->components = calloc(s->nComponents, sizeof(FMIInstance*));

    for (size_t i = 0; i < s->nComponents; i++) {
        mpack_node_t component = mpack_node_array_at(components, i);

        mpack_node_t name = mpack_node_map_cstr(component, "name");
        char* _name = mpack_node_cstr_alloc(name, 1024);

        mpack_node_t guid = mpack_node_map_cstr(component, "guid");
        char* _guid = mpack_node_cstr_alloc(guid, 1024);

        mpack_node_t modelIdentifier = mpack_node_map_cstr(component, "modelIdentifier");
        char* _modelIdentifier = mpack_node_cstr_alloc(modelIdentifier, 1024);

        char unzipdir[4069] = "";
        char componentResourcesDir[4069] = "";

#ifdef _WIN32
        PathCombine(unzipdir, resourcesDir, _modelIdentifier);
        PathCombine(componentResourcesDir, unzipdir, "resources");
#else
        sprintf(unzipdir, "%s/%s", resourcesDir, _modelIdentifier);
        sprintf(componentResourcesDir, "%s/%s", unzipdir, "resources");
#endif
        char componentResourcesUri[4069] = "";

        FMIPathToURI(componentResourcesDir, componentResourcesUri, 4096);

        char libraryPath[4069] = "";

        FMIPlatformBinaryPath(unzipdir, _modelIdentifier, FMIVersion2, libraryPath, 4096);

        FMIInstance* m = FMICreateInstance(_name, libraryPath, logFMIMessage, loggingOn ? logFunctionCall : NULL);

        if (!m) {
            return NULL;
        }

        m->userData = s;

        Component* c = calloc(1, sizeof(Component));

        if (FMI2Instantiate(m, componentResourcesUri, fmi2CoSimulation, _guid, visible, loggingOn) > FMIWarning) {
            return NULL;
        }

        c->instance = m;

        if (s->parallelDoStep) {
            c->doStep = false;
            c->terminate = false;
#ifdef _WIN32
            // TODO: check for invalid handles
            c->mutex = CreateMutexA(NULL, FALSE, NULL);
            c->thread = CreateThread(NULL, 0, instanceDoStep, c, 0, NULL);
#else
            // TODO: check return codes
            pthread_mutex_init(&c->mutex, NULL);
            pthread_create(&c->thread, NULL, &instanceDoStep, c);
#endif
        }

        s->components[i] = c;
    }

    mpack_node_t connections = mpack_node_map_cstr(root, "connections");

    s->nConnections = mpack_node_array_length(connections);

    s->connections = calloc(s->nConnections, sizeof(Connection));

    for (size_t i = 0; i < s->nConnections; i++) {
        mpack_node_t connection = mpack_node_array_at(connections, i);

        mpack_node_t type = mpack_node_map_cstr(connection, "type");
        s->connections[i].type = mpack_node_int(type);

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
        mpack_node_t variableTypeNode = mpack_node_map_cstr(variable, "type");
        FMIVariableType variableType = mpack_node_int(variableTypeNode);

        const bool hasStartValue = mpack_node_map_contains_cstr(variable, "start");

        mpack_node_t start;

        if (hasStartValue) {
            start = mpack_node_map_cstr(variable, "start");
        }

        s->variables[i].size = mpack_node_array_length(components);
        s->variables[i].ci = calloc(s->variables[i].size, sizeof(size_t));
        s->variables[i].vr = calloc(s->variables[i].size, sizeof(fmi2ValueReference));

        for (size_t j = 0; j < s->variables[i].size; j++) {

            mpack_node_t component = mpack_node_array_at(components, j);
            mpack_node_t valueReference = mpack_node_array_at(valueReferences, j);

            const size_t ci = mpack_node_u64(component);
            const fmi2ValueReference vr = mpack_node_u32(valueReference);

            if (hasStartValue) {

                fmi2Status status = fmi2OK;
                FMIInstance* m = s->components[ci]->instance;

                switch (variableType) {
                case FMIRealType: {
                    const fmi2Real value = mpack_node_double(start);
                    status = FMI2SetReal(m, &vr, 1, &value);
                    break;
                }
                case FMIIntegerType: {
                    const fmi2Integer value = mpack_node_int(start);
                    status = FMI2SetInteger(m, &vr, 1, &value);
                    break;
                }
                case FMIBooleanType: {
                    const fmi2Boolean value = mpack_node_bool(start);
                    status = FMI2SetBoolean(m, &vr, 1, &value);
                    break;
                }
                case FMIStringType: {
                    const fmi2String value = mpack_node_cstr_alloc(start, 2048);
                    status = FMI2SetString(m, &vr, 1, &value);
                    MPACK_FREE((void*)value);
                    break;
                }
                default:
                    // TODO: log this
                    // logMessage(NULL, instanceName, fmi2Fatal, "logError", "Unknown type ID for variable index %d: %d.", j, variableType);
                    return NULL;
                    break;
                }

                if (status > fmi2Warning) {
                    return NULL;
                }
            }

            s->variables[i].ci[j] = ci;
            s->variables[i].vr[j] = vr;
        }

    }

    // clean up and check for errors
    if (mpack_tree_destroy(&tree) != mpack_ok) {
        // TODO: log this
        // logger(NULL, instanceName, fmi2Error, "logError", "An error occurred decoding %s.", configFilename);
        return NULL;
    }

    return s;
}

#define CHECK_STATUS(S) status = S; if (status > FMIWarning) goto END

FMIStatus doStep(
    System* s,
    double  currentCommunicationPoint,
    double  communicationStepSize,
    bool    noSetFMUStatePriorToCurrentPoint) {

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < s->nConnections; i++) {

        fmi2Real realValue;
        fmi2Integer integerValue;
        fmi2Boolean booleanValue;
        fmi2String stringValue;
        Connection* k = &(s->connections[i]);
        FMIInstance* m1 = s->components[k->startComponent]->instance;
        FMIInstance* m2 = s->components[k->endComponent]->instance;
        fmi2ValueReference vr1 = k->startValueReference;
        fmi2ValueReference vr2 = k->endValueReference;

        switch (k->type) {
        case FMIRealType:
            CHECK_STATUS(FMI2GetReal(m1, &(vr1), 1, &realValue));
            CHECK_STATUS(FMI2SetReal(m2, &(vr2), 1, &realValue));
            break;
        case FMIIntegerType:
            CHECK_STATUS(FMI2GetInteger(m1, &(vr1), 1, &integerValue));
            CHECK_STATUS(FMI2SetInteger(m2, &(vr2), 1, &integerValue));
            break;
        case FMIBooleanType:
            CHECK_STATUS(FMI2GetBoolean(m1, &(vr1), 1, &booleanValue));
            CHECK_STATUS(FMI2SetBoolean(m2, &(vr2), 1, &booleanValue));
            break;
        case FMIStringType:
            CHECK_STATUS(FMI2GetString(m1, &(vr1), 1, &stringValue));
            CHECK_STATUS(FMI2SetString(m2, &(vr2), 1, &stringValue));
            break;

        default:
            break;
        }
    }

    if (s->parallelDoStep) {

        for (size_t i = 0; i < s->nComponents; i++) {
            Component* component = s->components[i];
#ifdef _WIN32
            WaitForSingleObject(component->mutex, INFINITE);
#else
            pthread_mutex_lock(&component->mutex);
#endif
            component->currentCommunicationPoint = currentCommunicationPoint;
            component->communicationStepSize = communicationStepSize;
            component->doStep = true;
#ifdef _WIN32
            ReleaseMutex(component->mutex);
#else
            pthread_mutex_unlock(&component->mutex);
#endif
        }

        for (size_t i = 0; i < s->nComponents; i++) {
            Component* component = s->components[i];
            bool waitForThread = true;
            fmi2Status status;

            while (waitForThread) {
#ifdef _WIN32
                WaitForSingleObject(component->mutex, INFINITE);
#else
                pthread_mutex_lock(&component->mutex);
#endif
                waitForThread = component->doStep;
                status = component->status;
#ifdef _WIN32
                ReleaseMutex(component->mutex);
#else
                pthread_mutex_unlock(&component->mutex);
#endif
            }

            CHECK_STATUS(status);
        }

    }
    else {

        for (size_t i = 0; i < s->nComponents; i++) {
            FMIInstance* m = s->components[i]->instance;
            CHECK_STATUS(FMI2DoStep(m, currentCommunicationPoint, communicationStepSize, noSetFMUStatePriorToCurrentPoint));
        }

    }

END:
    return status;
}

FMIStatus terminateSystem(System* s) {

    FMIStatus status = FMIOK;

    for (size_t i = 0; i < s->nComponents; i++) {

        Component* component = s->components[i];

        CHECK_STATUS(FMI2Terminate(component->instance));

        if (s->parallelDoStep) {
#ifdef _WIN32
            WaitForSingleObject(component->mutex, INFINITE);
            component->terminate = true;
            ReleaseMutex(component->mutex);
            WaitForSingleObject(component->thread, INFINITE);
#else
            pthread_mutex_lock(&component->mutex);
            component->terminate = true;
            pthread_mutex_unlock(&component->mutex);
            pthread_join(component->thread, NULL);
#endif
        }
    }

END:
    return status;
}

FMIStatus resetSystem(System* s) {

    FMIStatus status = FMIOK;

    s->time = 0;

    for (size_t i = 0; i < s->nComponents; i++) {
        FMIInstance* m = s->components[i]->instance;
        CHECK_STATUS(FMI2Reset(m));
    }
END:
    return status;
}

void freeSystem(System* s) {

    for (size_t i = 0; i < s->nComponents; i++) {
        Component* component = s->components[i];
        FMIInstance* m = component->instance;
        FMI2FreeInstance(m);
        FMIFreeInstance(m);
        if (s->parallelDoStep) {
#ifdef _WIN32
            CloseHandle(component->mutex);
            CloseHandle(component->thread);
#else
            pthread_mutex_destroy(&component->mutex);
            pthread_join(component->thread, NULL);
#endif
        }
        free(component);
    }

    free((void*)s->instanceName);
    free(s);
}
