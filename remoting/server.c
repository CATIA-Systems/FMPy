/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef WIN32
#   include <windows.h>
#   pragma warning(disable: 4996) /* Stop complaining about strdup() */
#else
#   include <dlfcn.h>
#endif
#include "process.h"
#include "remote.h"
#include "server.h"

//#define SERVER_DEBUG
#ifdef SERVER_DEBUG
#   include <stdio.h>
#   define SERVER_LOG(message, ...) do { printf("[SERVER] " message, ##__VA_ARGS__); fflush(stdout); } while(0)
#else
#   define SERVER_LOG(message, ...)
#endif

/*----------------------------------------------------------------------------
                                 L O G G E R
----------------------------------------------------------------------------*/

#define _LOG(server, ...)           server_logger(server, server->instance_name, ##__VA_ARGS__)
#define LOG_DEBUG(server, ...)      _LOG(server, fmi2OK, "[SERVER]", ##__VA_ARGS__)
#define LOG_WARNING(server, ...)    _LOG(server, fmi2Warning, "SERVER", ##__VA_ARGS__)
#define LOG_ERROR(server, ...)      _LOG(server, fmi2Error, "SERVER]", ##__VA_ARGS__)


static void server_logger(fmi2ComponentEnvironment componentEnvironment,
    fmi2String instanceName,
    fmi2Status status,
    fmi2String category,
    fmi2String message,
    ...) {
    server_t *server = (server_t*)componentEnvironment;
    va_list params;

    if (server) {
        remote_data_t* remote_data = server->communication->data;
        const size_t offset = strlen(remote_data->message);
        

        va_start(params, message);
        vsnprintf(remote_data->message + offset, REMOTE_MESSAGE_SIZE - offset, message, params);
        va_end(params);

        strncat(remote_data->message + offset, "\n", REMOTE_MESSAGE_SIZE - offset - strlen(remote_data->message + offset));
        remote_data->message[REMOTE_MESSAGE_SIZE-1] = '\0'; /* paranoia */
        

        SERVER_LOG("LOG: %s\n", remote_data->message + offset);
    } else {
        /* Early log message sent buggy FMU */
        printf("Buggy FMU message: ");
        va_start(params, message);
        vprintf(message, params);
        va_end(params);
        printf("\n");
    }
    return;
}


/*----------------------------------------------------------------------------
                            L O A D I N G   D L L
----------------------------------------------------------------------------*/

static void *library_symbol(library_t library, const char* symbol_name) {
    if (library)
#ifdef WIN32
        return (void *)GetProcAddress(library, symbol_name);
#else
        return dlsym(library, symbol_name);
#endif
    else
        return NULL;
}


static library_t library_load(const char* library_filename) {
    library_t handle;
    SERVER_LOG("Loading Dynamic Library `%s'\n", library_filename);
#ifdef WIN32
    handle = LoadLibraryA(library_filename);
#else
    handle = dlopen(library_filename, RTLD_LAZY | RTLD_LOCAL);
#endif

#ifdef SERVER_DEBUG
    if (!handle) 
        SERVER_LOG("Cannot load `%s'\n", library_filename);
    else
        SERVER_LOG("Loaded.\n");
#endif

    return handle;
}


static void library_unload(library_t library) {
    if (library) {
#ifdef WIN32
        FreeLibrary(library);
#else
        dlclose(library);
#endif
    }
}


static void map_entries(fmu_entries_t* entries, library_t library) {
#	define MAP(x) entries->x = (x ## TYPE*)library_symbol(library, #x); \
	SERVER_LOG("function %-30s: %s\n", "`" #x "'", (entries->x)?"found":"not implemented")

    MAP(fmi2GetTypesPlatform);  /* 0 */
    MAP(fmi2GetVersion);
    MAP(fmi2SetDebugLogging);
    MAP(fmi2Instantiate);
    MAP(fmi2FreeInstance);
    MAP(fmi2SetupExperiment);
    MAP(fmi2EnterInitializationMode);
    MAP(fmi2ExitInitializationMode);
    MAP(fmi2Terminate);
    MAP(fmi2Reset);
    MAP(fmi2GetReal); /* 10 */
    MAP(fmi2GetInteger);
    MAP(fmi2GetBoolean);
    MAP(fmi2GetString);
    MAP(fmi2SetReal);
    MAP(fmi2SetInteger);
    MAP(fmi2SetBoolean);
    MAP(fmi2SetString);
    MAP(fmi2GetFMUstate);
    MAP(fmi2SetFMUstate);
    MAP(fmi2FreeFMUstate); /* 20 */
    MAP(fmi2SerializedFMUstateSize);
    MAP(fmi2SerializeFMUstate);
    MAP(fmi2DeSerializeFMUstate);
    MAP(fmi2GetDirectionalDerivative);

    MAP(fmi2EnterEventMode);
    MAP(fmi2NewDiscreteStates);
    MAP(fmi2EnterContinuousTimeMode);
    MAP(fmi2CompletedIntegratorStep);
    MAP(fmi2SetTime);
    MAP(fmi2SetContinuousStates); /* 30 */
    MAP(fmi2GetDerivatives);
    MAP(fmi2GetEventIndicators);
    MAP(fmi2GetContinuousStates);
    MAP(fmi2GetNominalsOfContinuousStates);

    MAP(fmi2SetRealInputDerivatives);
    MAP(fmi2GetRealOutputDerivatives);
    MAP(fmi2DoStep);
    MAP(fmi2CancelStep);
    MAP(fmi2GetStatus);
    MAP(fmi2GetRealStatus); /* 40 */
    MAP(fmi2GetIntegerStatus);
    MAP(fmi2GetBooleanStatus);
    MAP(fmi2GetStringStatus);
#undef MAP
    return;
}


/*----------------------------------------------------------------------------
                                S E R V E R
----------------------------------------------------------------------------*/


static void server_free(server_t* server) {
    if (server->communication)
        communication_free(server->communication);
    library_unload(server->library);
#ifdef WIN32
    CloseHandle(server->parent_handle);
#endif
    free(server->instance_name);
    free(server);

    return;
}
    

static server_t* server_new(const char *library_filename, unsigned long ppid, const char *secret) {
    server_t* server;
    server = malloc(sizeof(*server));
    if (!server)
        return NULL;
    server->instance_name = NULL;
    server->is_debug = 0;
#ifdef WIN32
    server->parent_handle = OpenProcess(SYNCHRONIZE, FALSE, ppid);
#else
    server->parent_handle = ppid;
#endif
    server->library_filename = library_filename;
    server->library = NULL; /* Library will be loaded on demand */
    server->functions.logger = server_logger;
    server->functions.allocateMemory = calloc;
    server->functions.freeMemory = free;
    server->functions.stepFinished = NULL;
    server->functions.componentEnvironment = server;
    strncpy(server->shared_key, secret, sizeof(server->shared_key));
    SERVER_LOG("Server UUID for IPC: '%s'\n", server->shared_key);

    server->communication = communication_new(server->shared_key, REMOTE_DATA_SIZE, COMMUNICATION_SERVER);
    /* At this point Client and Server are Synchronized */


    return server;
}


/*-----------------------------------------------------------------------------
                             M A I N   L O O P
-----------------------------------------------------------------------------*/

static int is_parent_still_alive(const server_t *server) {
    return process_is_alive(server->parent_handle);
}


int main(int argc, char* argv[]) {
#ifndef WIN32
    setlinebuf(stdout);
    setlinebuf(stderr);
#endif
    SERVER_LOG("STARING...\n");
    if (argc != 4) {
        fprintf(stderr, "Usage: server <parent_process_id> <secret> <library_path>\n");
        return 1;
    }

    SERVER_LOG("Initializing...\n");
    server_t* server = server_new(argv[3], strtoul(argv[1], NULL, 10), argv[2]);
    if (!server) {
        SERVER_LOG("Initialize server. Exit.\n");
        return -1;
    }


    remote_data_t* remote_data = server->communication->data;
#define SERVER_DECODE_VAR(_n, _type)    REMOTE_DECODE_VAR(remote_data->data, _n, _type)
#define SERVER_DECODE_PTR(_n, _type)    REMOTE_DECODE_PTR(remote_data->data, _n, _type)
#define SERVER_DECODE_STR(_n)           REMOTE_DECODE_STR(remote_data->data, _n)
#define STATUS                          remote_data->status

    int wait_for_function = 1;
    while (wait_for_function) {

        /*
         * Watch dog !
         */
        SERVER_LOG("WAIT\n");
        while (communication_timedwaitfor_client(server->communication,COMMUNICATION_TIMEOUT_DEFAULT)) {
            if (!is_parent_still_alive(server)) {
                SERVER_LOG("Parent process died.\n");
                wait_for_function = 0;
                break;
            }
        }
        if (!wait_for_function)
            break;

        /*
         * Decode & execute function
         */


        remote_function_t function = remote_data->function;
        SERVER_LOG("RPC: %s | execute\n", remote_function_name(function));
        STATUS = -1; /* means that real function is not (yet?) called */

     
        switch (function) {
        case REMOTE_fmi2GetTypesPlatform:
        case REMOTE_fmi2GetVersion:
        case REMOTE_fmi2SetDebugLogging:
            LOG_ERROR(server, "Function '%s' is not implemented.", remote_function_name(function));
            STATUS = fmi2Error;
            break;

        case REMOTE_fmi2Instantiate:
            server->instance_name = strdup(SERVER_DECODE_STR(0));
            server->is_debug = SERVER_DECODE_VAR(5, fmi2Boolean);
            server->library = library_load(server->library_filename);
            if (!server->library)
                LOG_ERROR(server, "Cannot open DLL object '%s'. ", server->library_filename);
            map_entries(&server->entries, server->library);
            server->component = NULL;

            if (server->entries.fmi2Instantiate)
                server->component = server->entries.fmi2Instantiate(
                    SERVER_DECODE_STR(0),
                    SERVER_DECODE_VAR(1, fmi2Type),
                    SERVER_DECODE_STR(2),
                    SERVER_DECODE_STR(3),
                    &server->functions,
                    SERVER_DECODE_VAR(4, fmi2Boolean),
                    SERVER_DECODE_VAR(5, fmi2Boolean));
            
            if (!server->component) {
                LOG_ERROR(server, "Cannot instanciate FMU.");
                STATUS = fmi2Error;
            }
            else
                STATUS = fmi2OK;
            break;

        case REMOTE_fmi2FreeInstance:
            if (server->entries.fmi2FreeInstance) {
                server->entries.fmi2FreeInstance(server->component);
                STATUS = fmi2OK;
            }
            else {
                LOG_ERROR(server, "Function 'fmi2FreeInstance' not reachable.");
                STATUS = fmi2Error;
            }
            server->component = NULL;
            library_unload(server->library);
            server->library = NULL;

            wait_for_function = 0;
            break;

        case REMOTE_fmi2SetupExperiment:
            if (server->entries.fmi2SetupExperiment)
                STATUS = server->entries.fmi2SetupExperiment(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2Boolean),
                    SERVER_DECODE_VAR(1, fmi2Real),
                    SERVER_DECODE_VAR(2, fmi2Real),
                    SERVER_DECODE_VAR(3, fmi2Boolean),
                    SERVER_DECODE_VAR(4, fmi2Real));
            break;

        case REMOTE_fmi2EnterInitializationMode:
            if (server->entries.fmi2EnterInitializationMode)
               STATUS = server->entries.fmi2EnterInitializationMode(server->component);
            break;

        case REMOTE_fmi2ExitInitializationMode:
            if (server->entries.fmi2ExitInitializationMode)
                STATUS = server->entries.fmi2ExitInitializationMode(server->component);
            break;

        case REMOTE_fmi2Terminate:
            if (server->entries.fmi2Terminate)
                STATUS = server->entries.fmi2Terminate(server->component);
            break;

        case REMOTE_fmi2Reset:
            if (server->entries.fmi2Reset)
                STATUS = server->entries.fmi2Reset(server->component);
            break;

        case REMOTE_fmi2GetReal:
            if (server->entries.fmi2GetReal)
                STATUS = server->entries.fmi2GetReal(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, fmi2Real*));
            break;

        case REMOTE_fmi2GetInteger:
            if (server->entries.fmi2GetInteger)
                STATUS = server->entries.fmi2GetInteger(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, fmi2Integer*));
            break;

        case REMOTE_fmi2GetBoolean:
            if (server->entries.fmi2GetBoolean)
                STATUS = server->entries.fmi2GetBoolean(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, fmi2Boolean*));
            break;

        case REMOTE_fmi2GetString:
            if (server->entries.fmi2GetString) {
                portable_size_t nvr = SERVER_DECODE_VAR(1, portable_size_t);
                fmi2String* value = malloc(sizeof(*value) * nvr);

                STATUS = server->entries.fmi2GetString(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    nvr,
                    value);
                remote_encode_strings(value, SERVER_DECODE_PTR(2, char *), nvr);
                free((void *)value);
            }
            break;

        case REMOTE_fmi2SetReal:
            if (server->entries.fmi2SetReal)
                STATUS = server->entries.fmi2SetReal(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2Real*));
            break;

        case REMOTE_fmi2SetInteger:
            if (server->entries.fmi2SetInteger)
                STATUS = server->entries.fmi2SetInteger(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2Integer*));
            break;

        case REMOTE_fmi2SetBoolean:
            if (server->entries.fmi2SetBoolean)
                STATUS = server->entries.fmi2SetBoolean(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2Boolean*));
            break;

        case REMOTE_fmi2SetString:
            if (server->entries.fmi2SetString) {
                portable_size_t nvr = SERVER_DECODE_VAR(1, portable_size_t);
                fmi2String *value = malloc(sizeof(*value) * nvr);
                remote_decode_strings(SERVER_DECODE_PTR(2, const char *), value, nvr);

                STATUS = server->entries.fmi2SetString(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2ValueReference*),
                    nvr,
                    value);
                free((void *)value);
            }
            break;

        case REMOTE_fmi2GetFMUstate:
        case REMOTE_fmi2SetFMUstate:
        case REMOTE_fmi2FreeFMUstate:
        case REMOTE_fmi2SerializedFMUstateSize:
        case REMOTE_fmi2SerializeFMUstate:
        case REMOTE_fmi2DeSerializeFMUstate:
            STATUS = fmi2Error;
            break;

        case REMOTE_fmi2GetDirectionalDerivative:
            if (server->entries.fmi2GetDirectionalDerivative)
                STATUS = server->entries.fmi2GetDirectionalDerivative(
                    server->component,
                    SERVER_DECODE_PTR(0, const fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2ValueReference*),
                    SERVER_DECODE_VAR(3, portable_size_t),
                    SERVER_DECODE_PTR(4, const fmi2Real*),
                    SERVER_DECODE_PTR(5, fmi2Real*));
            break;

        case REMOTE_fmi2EnterEventMode:
            if (server->entries.fmi2EnterEventMode)
                STATUS = server->entries.fmi2EnterEventMode(server->component);
            break;

        case REMOTE_fmi2NewDiscreteStates:
            if (server->entries.fmi2NewDiscreteStates)
                STATUS = server->entries.fmi2NewDiscreteStates(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2EventInfo*));
            break;

        case REMOTE_fmi2EnterContinuousTimeMode:
            if (server->entries.fmi2EnterContinuousTimeMode)
                STATUS = server->entries.fmi2EnterContinuousTimeMode(server->component);
            break;

        case REMOTE_fmi2CompletedIntegratorStep:
            if (server->entries.fmi2CompletedIntegratorStep)
                STATUS = server->entries.fmi2CompletedIntegratorStep(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2Boolean),
                    SERVER_DECODE_PTR(1, fmi2Boolean*),
                    SERVER_DECODE_PTR(2, fmi2Boolean*));
            break;

        case REMOTE_fmi2SetTime:
            if (server->entries.fmi2SetTime)
                STATUS = server->entries.fmi2SetTime(
                    server->component,
                    SERVER_DECODE_VAR(0, const fmi2Real));
            break;

        case REMOTE_fmi2SetContinuousStates:
            if (server->entries.fmi2SetContinuousStates)
                STATUS = server->entries.fmi2SetContinuousStates(
                    server->component,
                    SERVER_DECODE_PTR(0, const fmi2Real*),
                    SERVER_DECODE_VAR(1, portable_size_t));
            break;

        case REMOTE_fmi2GetDerivatives:
            if (server->entries.fmi2GetDerivatives)
                STATUS = server->entries.fmi2GetDerivatives(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2Real*),
                    SERVER_DECODE_VAR(1, portable_size_t));
            break;

        case REMOTE_fmi2GetEventIndicators:
            if (server->entries.fmi2GetEventIndicators)
              STATUS = server->entries.fmi2GetEventIndicators(
                  server->component,
                  SERVER_DECODE_PTR(0, fmi2Real*),
                  SERVER_DECODE_VAR(1, portable_size_t));
            break;

        case REMOTE_fmi2GetContinuousStates:
            if (server->entries.fmi2GetContinuousStates)
                STATUS = server->entries.fmi2GetContinuousStates(
                    server->component,
                    SERVER_DECODE_PTR(0, fmi2Real*),
                    SERVER_DECODE_VAR(1, portable_size_t));
            break;

        case REMOTE_fmi2GetNominalsOfContinuousStates:
            if (server->entries.fmi2GetNominalsOfContinuousStates)
            STATUS = server->entries.fmi2GetNominalsOfContinuousStates(
                server->component,
                SERVER_DECODE_PTR(0, fmi2Real*),
                SERVER_DECODE_VAR(1, portable_size_t));
            break;

        case REMOTE_fmi2SetRealInputDerivatives:
            if (server->entries.fmi2SetRealInputDerivatives)
                STATUS = server->entries.fmi2SetRealInputDerivatives(
                    server->component,
                    SERVER_DECODE_PTR(0, const fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2Integer*),
                    SERVER_DECODE_PTR(3, const fmi2Real*));
            break;

        case REMOTE_fmi2GetRealOutputDerivatives:
            if (server->entries.fmi2GetRealOutputDerivatives)
                STATUS = server->entries.fmi2GetRealOutputDerivatives(
                    server->component,
                    SERVER_DECODE_PTR(0, const fmi2ValueReference*),
                    SERVER_DECODE_VAR(1, portable_size_t),
                    SERVER_DECODE_PTR(2, const fmi2Integer*),
                    SERVER_DECODE_PTR(3, fmi2Real*));
            break;

        case REMOTE_fmi2DoStep:
            if (server->entries.fmi2DoStep)
                STATUS = server->entries.fmi2DoStep(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2Real),
                    SERVER_DECODE_VAR(1, fmi2Real),
                    SERVER_DECODE_VAR(2, fmi2Boolean));
            break;

        case REMOTE_fmi2CancelStep:
            if (server->entries.fmi2CancelStep)
                STATUS = server->entries.fmi2CancelStep(server->component);
            break;

        case REMOTE_fmi2GetStatus:
            if (server->entries.fmi2GetStatus)
                STATUS = server->entries.fmi2GetStatus(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2StatusKind),
                    SERVER_DECODE_PTR(1, fmi2Status*));
            break;

        case REMOTE_fmi2GetRealStatus:
            if (server->entries.fmi2GetRealStatus)
                STATUS = server->entries.fmi2GetRealStatus(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2StatusKind),
                    SERVER_DECODE_PTR(1, fmi2Real*));
            break;

        case REMOTE_fmi2GetIntegerStatus:
            if (server->entries.fmi2GetIntegerStatus)
                STATUS = server->entries.fmi2GetIntegerStatus(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2StatusKind),
                    SERVER_DECODE_PTR(1, fmi2Integer*));
            break;

        case REMOTE_fmi2GetBooleanStatus:
            if (server->entries.fmi2GetBooleanStatus)
                STATUS = server->entries.fmi2GetBooleanStatus(
                    server->component,
                    SERVER_DECODE_VAR(0, fmi2StatusKind),
                    SERVER_DECODE_PTR(1, fmi2Boolean*));
            break;

        case REMOTE_fmi2GetStringStatus:
            if (server->entries.fmi2GetStringStatus)
                STATUS = fmi2Error;
            break;
        }


        /*
         * Acknoledge the client side !
         */
        if (STATUS < 0) {
            LOG_ERROR(server, "Function '%s' unreachable.", remote_function_name(function));
            STATUS = fmi2Error;
        }
        SERVER_LOG("RPC: %s | processed.\n", remote_function_name(function));
        communication_server_ready(server->communication);
    }

    /*
     * End of loop
     */
    server_free(server);
    SERVER_LOG("Exit.\n");


    return 0;
}
