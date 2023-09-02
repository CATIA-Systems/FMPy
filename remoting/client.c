/*    ___                                               __   __              
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com. 
 *  This code is released under the 2-Clause BSD license.
 */
#include "config.h"

#ifdef WIN32
#   include <io.h>
#else
#   define _GNU_SOURCE  /* to access to dladdr */
#   include <dlfcn.h>
#endif
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <fmi2Functions.h>

#include "client.h"
#include "communication.h"
#include "process.h"


//#define CLIENT_DEBUG
#ifdef CLIENT_DEBUG
#   include <stdio.h>
#   define CLIENT_LOG(message, ...) printf("[CLIENT] " message, ##__VA_ARGS__)
#else
#   define CLIENT_LOG(message, ...)
#endif


/*----------------------------------------------------------------------------
                                 L O G G E R 
----------------------------------------------------------------------------*/

#define _LOG(client, level, ...)    client_logger(client, level, ##__VA_ARGS__)
#define LOG_DEBUG(client, ...)      _LOG(client, fmi2OK, ##__VA_ARGS__)
#define LOG_WARNING(client, ...)    _LOG(client, fmi2Warning, ##__VA_ARGS__)
#define LOG_ERROR(client, ...)      _LOG(client, fmi2Error, ##__VA_ARGS__)

static char *next_cr(char *message) {
    char *cr = message;
    while (*cr) {
        if (*cr == '\n') {
            *cr = '\0';
            return cr + 1;
        }
        cr++;
    }
    return cr;
}


static void client_logger(const client_t* client, fmi2Status level, const char* message, ...) {
    if (client->functions->logger) {
        char full_message[REMOTE_MESSAGE_SIZE];
        va_list ap;

        va_start(ap, message);
        vsnprintf(full_message, REMOTE_MESSAGE_SIZE, message, ap);
        full_message[REMOTE_MESSAGE_SIZE - 1] = '\0';
        va_end(ap);

        if ((level != fmi2OK) || (client->is_debug)) {
            char* line = full_message;
            while (line[0]) {
                char* next_line = next_cr(line);
                CLIENT_LOG("LOG: %s\n", line);
                client->functions->logger(client->functions->componentEnvironment, client->instance_name,
                    level, NULL, "%s", line);
                line = next_line;
            }
        }
    }

    return;
}


/*----------------------------------------------------------------------------
              R E M O T E   P R O C E D U R E   C A L L
----------------------------------------------------------------------------*/

static int is_server_still_alive(const client_t *client) {
    return process_is_alive(client->server_handle);
}


static fmi2Status make_rpc(client_t* client, remote_function_t function) {
    remote_data_t *remote_data = client->communication->data;

    fmi2Status status = (fmi2Status)-1;
    
    /* Flush message log */
    remote_data->message[0] = '\0';

    CLIENT_LOG("RPC: %s\n", remote_function_name(function));
    remote_data->function = function;

    /* Wait for answer */
    communication_client_ready(client->communication);
    while (communication_timedwaitfor_server(client->communication, COMMUNICATION_TIMEOUT_DEFAULT)) {
        if (!is_server_still_alive(client)) {
            LOG_ERROR(client, "Server unexpectly died.");
            return fmi2Fatal;
        }
        LOG_DEBUG(client, "Waiting for server...");
    }

    status = remote_data->status; 
    CLIENT_LOG("RPC: %s | reply = %d\n", remote_function_name(function), status);

    if (remote_data->message[0]) {
        client_logger(client, status, "%s", remote_data->message);
        remote_data->message[0] = '\0'; /* Flush message log */
    }

    return status;
}


/*----------------------------------------------------------------------------
                     S P A W N I N G    S E R V E R
----------------------------------------------------------------------------*/

static char* dirname(char* path) {
    for(size_t i = strlen(path); i > 0; i -= 1)
#ifdef WIN32
        if (path[i] == '\\') {
#else
        if (path[i] == '/') {
#endif
            path[i] = '\0';
            return path + i + 1;
        }
    return path;
}
 

static int get_server_bitness(void) {
    /* current process (calling this dll) is 64bits, the server is 32 bits */
    if (sizeof(void*) == 8)
        return 32;
    else
        return 64;
}


static int client_module_path(char path[MAX_PATH])  {
#ifdef WIN32
    HMODULE hm = NULL;

    if (GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCSTR)&fmi2Instantiate, &hm) == 0) {
            return -1;
    }
    if (GetModuleFileName(hm, path, MAX_PATH) == 0) {
            return -2;
    }
#else
    Dl_info info;
    if (dladdr(fmi2Instantiate, &info) == 0)
        return -1;

    /* on linux, sometime info.dli does not contain an absolute path */
    if (info.dli_fname[0] != '/') {
        getcwd(path, MAX_PATH);
        strncat(path, "/", MAX_PATH - strlen(path));
        strncat(path, info.dli_fname, MAX_PATH - strlen(path));
    } else
        strncpy(path, info.dli_fname, MAX_PATH);
#endif
    return 0;
}




static int get_server_argv(client_t *client, char *argv[]) {
    char* model_identifier;
    char path[MAX_PATH];

    if (client_module_path(path))
        return -1;

    model_identifier = dirname(path);
    dirname(path);

    argv[0] = malloc(MAX_PATH*2);
    argv[1] = malloc(16);
    argv[2] = malloc(COMMUNICATION_KEY_LEN);
    argv[3] = malloc(MAX_PATH*2);

    snprintf(argv[0], MAX_PATH*2, "%s" CONFIG_DIR_SEP CONFIG_FMI_BIN "%d" CONFIG_DIR_SEP "server_sm" CONFIG_EXE_SUFFIXE,
             path, get_server_bitness());    
    snprintf(argv[1], 16, "%lu", process_current_id());
    strcpy(argv[2], client->shared_key);
    snprintf(argv[3], MAX_PATH*2, "%s" CONFIG_DIR_SEP CONFIG_FMI_BIN "%d" CONFIG_DIR_SEP "%s",
             path, get_server_bitness(), model_identifier);

    return 0;
}


static int spawn_server(client_t *client) {
    char *argv[5];

    if (get_server_argv(client, argv))
        return -1;
    argv[4] = NULL;

    LOG_DEBUG(client, "Starting remoting server. (Command: %s %s %s %s)", argv[0], argv[1], argv[2], argv[3]);

    client->server_handle = process_spawn(argv);

    free(argv[0]);
    free(argv[1]);
    free(argv[2]);
    free(argv[3]);

    if (! client->server_handle) {
        LOG_ERROR(client, "Failed to start server.");
        return -2;
    }

    return 0;
}


static void client_new_key(client_t *client) {
    snprintf(client->shared_key, sizeof(client->shared_key), "/FMU%lu", process_current_id());

    strcpy(client->shared_key, "/FMU");
    srand((unsigned int) time(NULL)+process_current_id());
    for(int i=strlen(client->shared_key); i<COMMUNICATION_KEY_LEN-1; i += 1) {
           client->shared_key[i] = 'a' + (rand() % 26);
    }
    client->shared_key[COMMUNICATION_KEY_LEN-1] = '\0'; 
    CLIENT_LOG("UUID for IPC: '%s'\n", client->shared_key);

    return;
}


static client_t* client_new(const char *instanceName, const fmi2CallbackFunctions* functions,
    int loggingOn) {
    client_t* client = malloc(sizeof(*client));
    client->functions = functions;
    client->instance_name = strdup(instanceName);
    client->is_debug = loggingOn;

    LOG_DEBUG(client, "FMU Remoting Interface version %s", REMOTING_VERSION);
    client_new_key(client);


    client->communication = communication_new(client->shared_key, REMOTE_DATA_SIZE, COMMUNICATION_CLIENT);
    if (!client->communication) {
        LOG_ERROR(client, "Unable to create SHM");
        return NULL;
    }

    if (spawn_server(client) < 0)
        return NULL;

    CLIENT_LOG("Waiting for server to be ready...\n");
    if (communication_timedwaitfor_server(client->communication, 15000))
        return NULL; /* Cannot launch server */
    
    return client;
}


static void client_free(client_t *client) {
    process_close_handle(client->server_handle);
    free(client->instance_name);
    communication_free(client->communication);
    free(client);

    return;
}


/*----------------------------------------------------------------------------
                       F M I 2   F O R W A R D I N G
----------------------------------------------------------------------------*/

#define CLIENT_CLEAR_ARGS(_nb)              REMOTE_CLEAR_ARGS(((remote_data_t *)client->communication->data)->data, _nb)
#define CLIENT_DATA                         ((remote_data_t *)client->communication->data)->data
#define CLIENT_ENCODE_VAR(_n, _var)         REMOTE_ENCODE_VAR(CLIENT_DATA, _n, _var)
#define CLIENT_ENCODE_STR(_n, _ptr)         REMOTE_ENCODE_STR(CLIENT_DATA, _n, _ptr)
#define CLIENT_ENCODE_PTR(_n, _ptr, _size)  REMOTE_ENCODE_PTR(CLIENT_DATA, _n, _ptr, _size)
#define CLIENT_ARG_PTR(_n)                  REMOTE_ARG_PTR(CLIENT_DATA, _n)
#define NOT_IMPLEMENTED                     LOG_ERROR(client, "Function not implemented"); return fmi2Error;


fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID,
                              fmi2String fmuResourceLocation, const fmi2CallbackFunctions* functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn) {
    client_t *client = client_new(instanceName, functions, loggingOn);
    if (!client)
        return NULL;

    CLIENT_ENCODE_STR(0, client->instance_name);
    CLIENT_ENCODE_VAR(1, fmuType);
    CLIENT_ENCODE_STR(2, fmuGUID);
    CLIENT_ENCODE_STR(3, fmuResourceLocation);
    CLIENT_ENCODE_VAR(4, visible);
    CLIENT_ENCODE_VAR(5, loggingOn);
    
    fmi2Status status = make_rpc(client, REMOTE_fmi2Instantiate);

    if ((status != fmi2Warning) && (status != fmi2OK)) {
        client_free(client);
        return NULL;
    }

    return (fmi2Component)client;
}


void fmi2FreeInstance(fmi2Component c) {
    client_t* client = (client_t*)c;

    make_rpc(client, REMOTE_fmi2FreeInstance);
    process_waitfor(client->server_handle);
    client_free(client);
    
    return;
}


const char* fmi2GetTypesPlatform() {
    return fmi2TypesPlatform;
}


const char* fmi2GetVersion() {
    return fmi2Version;
}

/* Enter and exit initialization mode, terminate and reset */
fmi2Status fmi2SetupExperiment(fmi2Component c, fmi2Boolean toleranceDefined, fmi2Real tolerance, fmi2Real startTime, fmi2Boolean stopTimeDefined, fmi2Real stopTime) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, toleranceDefined);
    CLIENT_ENCODE_VAR(1, tolerance);
    CLIENT_ENCODE_VAR(2, startTime);
    CLIENT_ENCODE_VAR(3, stopTimeDefined);
    CLIENT_ENCODE_VAR(4, stopTime);

    fmi2Status status = make_rpc(client, REMOTE_fmi2SetupExperiment);

    return status;
}


fmi2Status fmi2EnterInitializationMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2EnterInitializationMode);
}


fmi2Status fmi2ExitInitializationMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2ExitInitializationMode);
}


fmi2Status fmi2Terminate(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2Terminate);
}


fmi2Status fmi2Reset(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2Reset);
}


/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Real) > REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2GetReal message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetReal);

    memcpy(value, CLIENT_ARG_PTR(2), sizeof(fmi2Real) * nvr);

#ifdef CLIENT_DEBUG
    LOG_DEBUG(client, "fmi2GetReal: (status = %d), getting %d values:", status, nvr);
    for (size_t i = 0; i < nvr; i += 1) {
        LOG_DEBUG(client, "fmi2GetReal: #r%d# = %e", vr[i], value[i]);
    }
#endif
    return status;
}


fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Integer) >= REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2GetInteger message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetInteger);

    memcpy(value, CLIENT_ARG_PTR(2), sizeof(fmi2Integer) * nvr);

    return status;
}


fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Boolean) >= REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2GetBoolean message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetBoolean);

    memcpy(value, CLIENT_ARG_PTR(2), sizeof(fmi2Boolean) * nvr);

    return status;
}


fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetString);

    remote_decode_strings(CLIENT_ARG_PTR(2), value, nvr);

    return status;
}


fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Real) >= REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2SetReal message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

#ifdef CLIENT_DEBUG
    LOG_DEBUG(client, "fmi2SetReal: setting %d values:", nvr);
    for (size_t i = 0; i < nvr; i += 1) {
        LOG_DEBUG(client, "fmi2SetReal: #r%d# = %e", vr[i], value[i]);
    }
#endif
    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    CLIENT_ENCODE_PTR(2, value, nvr);

    return make_rpc(client, REMOTE_fmi2SetReal);
}


fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Integer) >= REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2SetInteger message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    CLIENT_ENCODE_PTR(2, value, nvr);

    return make_rpc(client, REMOTE_fmi2SetInteger);
}


fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    if (nvr * sizeof(fmi2Boolean) >= REMOTE_ARG_SIZE) {
        LOG_ERROR(client, "fmi2SetBoolean message is to big. Contact fmutool maintainer.");
        return fmi2Error;
    }

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    CLIENT_ENCODE_PTR(2, value, nvr);

    return make_rpc(client, REMOTE_fmi2SetBoolean);
}


fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    remote_encode_strings(value, CLIENT_ARG_PTR(2), nvr);

    return make_rpc(client, REMOTE_fmi2SetString);
}


/* Getting and setting the internal FMU state */
fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t* size) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte none[], size_t size) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


fmi2Status  fmi2SetDebugLogging(fmi2Component c,
    fmi2Boolean loggingOn,
    size_t nCategories,
    const fmi2String categories[]) {
    return fmi2OK;
}


fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED
}


/* Getting partial derivatives */
fmi2Status fmi2GetDirectionalDerivative(fmi2Component c, const fmi2ValueReference vUnknown_ref[], size_t nUnknown, const fmi2ValueReference vKnown_ref[], size_t nKnown, const fmi2Real dvKnown[], fmi2Real dvUnknown[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nUnknown = (portable_size_t)nUnknown;
    portable_size_t portable_nKnown = (portable_size_t)nKnown;

    CLIENT_ENCODE_PTR(0, vUnknown_ref, nUnknown);
    CLIENT_ENCODE_VAR(1, portable_nUnknown);
    CLIENT_ENCODE_PTR(2, vKnown_ref, nKnown);
    CLIENT_ENCODE_VAR(3, portable_nKnown);
    CLIENT_ENCODE_PTR(4, dvKnown, nKnown);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetDirectionalDerivative);

    memcpy(dvUnknown, CLIENT_ARG_PTR(5), sizeof(fmi2Real) * nKnown);

    return status;
}


/*
 * Types for Functions for FMI2 for Model Exchange
 */

/* Enter and exit the different modes */
fmi2Status fmi2EnterEventMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2EnterEventMode);
}


fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) {
    client_t* client = (client_t*)c;

    fmi2Status status = make_rpc(client, REMOTE_fmi2NewDiscreteStates);

    memcpy(eventInfo, CLIENT_ARG_PTR(0), sizeof(fmi2EventInfo));

    return status;
}


fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2EnterContinuousTimeMode);
}


fmi2Status fmi2CompletedIntegratorStep(fmi2Component c,
    fmi2Boolean  noSetFMUStatePriorToCurrentPoint, fmi2Boolean* enterEventMode,
    fmi2Boolean* terminateSimulation) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, noSetFMUStatePriorToCurrentPoint);

    fmi2Status status = make_rpc(client, REMOTE_fmi2CompletedIntegratorStep);

    memcpy(enterEventMode, CLIENT_ARG_PTR(1), sizeof(fmi2Boolean));
    memcpy(terminateSimulation, CLIENT_ARG_PTR(2), sizeof(fmi2Boolean));

    return status;
}


/* Providing independent variables and re-initialization of caching */
fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, time);

    return make_rpc(client, REMOTE_fmi2EnterEventMode);
}


fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nx = (portable_size_t)nx;

    CLIENT_ENCODE_PTR(0, x, nx);
    CLIENT_ENCODE_VAR(1, portable_nx);

    return make_rpc(client, REMOTE_fmi2SetContinuousStates);
}


/* Evaluation of the model equations */
fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nx = (portable_size_t)nx;

    CLIENT_ENCODE_VAR(1, portable_nx);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetDerivatives);

    memcpy(derivatives, CLIENT_ARG_PTR(0), sizeof(fmi2Real) * nx);

    return status;
}


fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {
    client_t* client = (client_t*)c;
    portable_size_t portable_ni = (portable_size_t)ni;

    CLIENT_ENCODE_VAR(1, portable_ni);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetEventIndicators);

    memcpy(eventIndicators, CLIENT_ARG_PTR(0), sizeof(fmi2Real) * ni);

    return status;
}


fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t nx) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nx = (portable_size_t)nx;

    CLIENT_ENCODE_VAR(1, portable_nx);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetContinuousStates);

    memcpy(x, CLIENT_ARG_PTR(0), sizeof(fmi2Real) * nx);

    return status;
}


fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nx = (portable_size_t)nx;

    CLIENT_ENCODE_VAR(1, portable_nx);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetNominalsOfContinuousStates);

    memcpy(x_nominal, CLIENT_ARG_PTR(0), sizeof(fmi2Real) * nx);

    return status;
}


/*
 * Types for Functions for FMI2 for Co-Simulation
 */

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    CLIENT_ENCODE_PTR(2, order, nvr);
    CLIENT_ENCODE_PTR(3, value, nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2SetRealInputDerivatives);

    return status;
}


fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) {
    client_t* client = (client_t*)c;
    portable_size_t portable_nvr = (portable_size_t)nvr;

    CLIENT_ENCODE_PTR(0, vr, nvr);
    CLIENT_ENCODE_VAR(1, portable_nvr);
    CLIENT_ENCODE_PTR(2, order, nvr);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetRealOutputDerivatives);

    memcpy(value, CLIENT_ARG_PTR(3), sizeof(fmi2Real) * nvr);

    return status;
}


fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, currentCommunicationPoint);
    CLIENT_ENCODE_VAR(1, communicationStepSize);
    CLIENT_ENCODE_VAR(2, noSetFMUStatePriorToCurrentPoint);

    return make_rpc(client, REMOTE_fmi2DoStep);
}


fmi2Status fmi2CancelStep(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, REMOTE_fmi2CancelStep);
}


/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, s);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetStatus);

    memcpy(value, CLIENT_ARG_PTR(1), sizeof(fmi2Status));

    return status;
}


fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, s);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetRealStatus);

    memcpy(value, CLIENT_ARG_PTR(1), sizeof(fmi2Real));

    return status;
}


fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, s);;

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetIntegerStatus);

    memcpy(value, CLIENT_ARG_PTR(1), sizeof(fmi2Integer));

    return status;
}


fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
    client_t* client = (client_t*)c;

    CLIENT_ENCODE_VAR(0, s);

    fmi2Status status = make_rpc(client, REMOTE_fmi2GetBooleanStatus);

    memcpy(value, CLIENT_ARG_PTR(1), sizeof(fmi2Boolean));

    return status;
}


fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String* value) {
    client_t* client = (client_t*)c;

    NOT_IMPLEMENTED

}
