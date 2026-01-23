#include "config.h"

#ifdef WIN32
#   include <io.h>
#   define strdup _strdup
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
#include "version.h"

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
#define __NOT_IMPLEMENTED__     LOG_ERROR(client, "Function is not implemented"); return fmi2Error;

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
        char full_message[COMMUNICATION_MESSAGE_SIZE];
        va_list ap;

        va_start(ap, message);
        vsnprintf(full_message, COMMUNICATION_MESSAGE_SIZE, message, ap);
        full_message[COMMUNICATION_MESSAGE_SIZE - 1] = '\0';
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


static fmi2Status make_rpc(client_t* client, rpc_function_t function) {
    communication_shm_t *remote_data = client->communication->shm;

    fmi2Status status = (fmi2Status)-1;
    
    /* Flush message log */
    remote_data->message[0] = '\0';

    CLIENT_LOG("RPC: %d\n", function);
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
    CLIENT_LOG("RPC: %d | reply = %d\n", function, status);
    if (remote_data->message[0]) {
        client_logger(client, fmi2Warning, "%s", remote_data->message);
        remote_data->message[0] = '\0'; /* Flush message log */
    }

    return status;
}


/*----------------------------------------------------------------------------
                     S P A W N I N G    S E R V E R
----------------------------------------------------------------------------*/


static char *dirname(char* path) {
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


static char* file_extension(char* filename) {
    for (size_t i = strlen(filename); i > 0; i -= 1)
        if (filename[i] == '.') {
            filename[i] = '\0';
            return filename + i + 1;
        }
    return filename;
}
 

static int get_client_bitness(void) {
    /* current process (calling this dll) is 64bits, the server is 32 bits */
    if (sizeof(void*) == 8)
        return 64;
    else
        return 32;
}


static int get_opposite_bitness(void) {
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


static int is_file(const char* path) {
    FILE* fp;
    if ((fp = fopen(path, "r"))) {
        fclose(fp);
        return 1;
    }
    return 0;
}


static int get_server_argv(client_t *client, char *argv[]) {
    char *library_name;
    char *extension;
    char path[MAX_PATH];
    int bitness;

    if (client_module_path(path))
        return -1;

    library_name = dirname(path); /* path now contains .../binaries/<os> */
    dirname(path);  /* path now contain .../binaries */
    extension = file_extension(library_name);

    argv[0] = malloc(MAX_PATH*2);
    argv[1] = malloc(16);
    argv[2] = malloc(COMMUNICATION_KEY_LEN);
    argv[3] = malloc(MAX_PATH*2);
    argv[4] = malloc(16);
    argv[5] = malloc(16);
    argv[6] = malloc(16);

    bitness = get_client_bitness();
    snprintf(argv[3], MAX_PATH * 2, "%s" CONFIG_DIR_SEP CONFIG_FMI_BIN "%d" CONFIG_DIR_SEP "%s-remoted.%s",
        path, bitness, library_name, extension);

    if (! is_file(argv[3])) {
        bitness = get_opposite_bitness();
        snprintf(argv[3], MAX_PATH * 2, "%s" CONFIG_DIR_SEP CONFIG_FMI_BIN "%d" CONFIG_DIR_SEP "%s.%s",
            path, bitness, library_name, extension);
    }
 
    snprintf(argv[0], MAX_PATH * 2, "%s" CONFIG_DIR_SEP CONFIG_FMI_BIN "%d" CONFIG_DIR_SEP "server_sm" CONFIG_EXE_SUFFIX,
        path, bitness);

    snprintf(argv[1], 16, "%lu", process_current_id());
    strcpy(argv[2], client->shared_key);

    snprintf(argv[4], 16, "%lu", client->communication->nb_reals);
    snprintf(argv[5], 16, "%lu", client->communication->nb_integers);
    snprintf(argv[6], 16, "%lu", client->communication->nb_booleans);

    return 0;
}


static int spawn_server(client_t *client) {
    char *argv[8];

    if (get_server_argv(client, argv))
        return -1;
    argv[7] = NULL;


    CLIENT_LOG("Starting remoting server. (Command: %s %s %s %s %s %s %s)\n", argv[0], argv[1], argv[2], argv[3], argv[4], argv[5], argv[6]);
    LOG_DEBUG(client, "Starting remoting server. (Command: %s %s %s %s %s %s %s)", argv[0], argv[1], argv[2], argv[3], argv[4], argv[5], argv[6]);

    client->server_handle = process_spawn(argv);

    free(argv[0]);
    free(argv[1]);
    free(argv[2]);
    free(argv[3]);
    free(argv[4]);
    free(argv[5]);
    free(argv[6]);

    if (! client->server_handle) {
        LOG_ERROR(client, "Failed to start server.");
        return -2;
    }

    return 0;
}

/* This is the basic CRC-32 calculation with some optimization but no
table lookup. The the byte reversal is avoided by shifting the crc reg
right instead of left and by using a reversed 32-bit word to represent
the polynomial.
   When compiled to Cyclops with GCC, this function executes in 8 + 72n
instructions, where n is the number of bytes in the input message. It
should be doable in 4 + 61n instructions.
   If the inner loop is strung out (approx. 5*8 = 40 instructions),
it would take about 6 + 46n instructions. */

static unsigned int crc32b(const unsigned char* message) {
    int i, j;
    unsigned int byte, crc, mask;

    i = 0;
    crc = 0xFFFFFFFF;
    while (message[i] != 0) {
        byte = message[i];            // Get next byte.
        crc = crc ^ byte;
        for (j = 7; j >= 0; j--) {    // Do eight times.
            if (crc & 1)
                mask = 0xEDB88320;
            else
                mask = 0x00000000;
            crc = (crc >> 1) ^ mask;
        }
        i = i + 1;
    }
    return ~crc;
}


static void client_new_key(client_t *client, const char * fmuResourceLocation) {
    snprintf(client->shared_key, COMMUNICATION_KEY_LEN, "/FMU%x", crc32b((const unsigned char *)fmuResourceLocation));
    CLIENT_LOG("UUID for IPC: '%s'\n", client->shared_key);

    return;
}


static void client_free(client_t* client) {
    process_close_handle(client->server_handle);
    free(client->instance_name);
    communication_free(client->communication);
    free(client);

    return;
}


static client_t* client_new(const char *filename, const char *instanceName, const fmi2CallbackFunctions* functions,
    int loggingOn, const char * fmuResourceLocation) {
    client_t* client = malloc(sizeof(*client));
    FILE* fp;
    unsigned long nb_reals, nb_integers, nb_booleans;
    client->functions = functions;
    client->instance_name = strdup(instanceName);
    client->is_debug = loggingOn;

    LOG_DEBUG(client, "FMU Remoting Interface version %s", VERSION_TAG);
    client_new_key(client, fmuResourceLocation);

    fp = fopen(filename, "rt");
    if (!fp) {
        LOG_ERROR(client, "Unable to open '%s'.", filename);
        free(client);
        return NULL;
    }

    if (fscanf(fp, "%lu %lu %lu ", &nb_reals, &nb_integers, &nb_booleans) < 3) {
        LOG_ERROR(client, "Unable read header.");
        fclose(fp);
        free(client);
        return NULL;
    }
    client->communication = communication_new(client->shared_key, nb_reals, nb_integers, nb_booleans, COMMUNICATION_CLIENT);
    if (!client->communication) {
        LOG_ERROR(client, "Unable to create SHM");
        return NULL;
    }
        
    communication_data_initialize(&client->data, client->communication);
    for (unsigned long i = 0; i < nb_reals; i += 1) {
        if (fscanf(fp, "%u ", &client->data.reals.vr[i]) < 1) {
            LOG_ERROR(client, "Unable to read REALS VR's.");
            fclose(fp);
            client_free(client);
            return NULL;
        }
        client->data.reals.changed[i] = false;
        client->data.reals.value[i] = 0.0;
    }
    for (unsigned long i = 0; i < nb_integers; i += 1) {
        if (fscanf(fp, "%u ", &client->data.integers.vr[i]) < 1) {
            LOG_ERROR(client, "Unable to read INTEGERS VR's.");
            fclose(fp);
            client_free(client);
            return NULL;
        }
        client->data.integers.changed[i] = false;
        client->data.integers.value[i] = 0;
    }
    for (unsigned long i = 0; i < nb_booleans; i += 1) {
        if (fscanf(fp, "%u ", &client->data.booleans.vr[i]) < 1) {
            LOG_ERROR(client, "Unable to read BOOLEANS VR's.");
            fclose(fp);
            client_free(client);
            return NULL;
        }
        client->data.booleans.changed[i] = false;
        client->data.booleans.value[i] = 0;
    }
    fclose(fp);

    if (spawn_server(client) < 0)
        return NULL;

    CLIENT_LOG("Waiting for server to be ready...\n");
    if (communication_timedwaitfor_server(client->communication, 15000)) {
        LOG_ERROR(client, "Server did not respond.");
        client_free(client);
        return NULL; /* Cannot launch server */
    }

    return client;
}


/*----------------------------------------------------------------------------
                       F M I 2   F O R W A R D I N G
----------------------------------------------------------------------------*/


fmi2Component fmi2Instantiate(fmi2String instanceName, fmi2Type fmuType, fmi2String fmuGUID,
                              fmi2String fmuResourceLocation, const fmi2CallbackFunctions* functions,
                              fmi2Boolean visible, fmi2Boolean loggingOn) {
    char filename[MAX_PATH];
    if (strncmp(fmuResourceLocation, "file://", 7) == 0)
        fmuResourceLocation += 7;
    if (fmuResourceLocation[0] == '/')
        fmuResourceLocation += 1;                  
    strncpy(filename, fmuResourceLocation, sizeof(filename));
    strncat(filename, "/remoting_table.txt", sizeof(filename)-strlen(filename)-1);
    filename[sizeof(filename)-1] = '\0';
    client_t *client = client_new(filename, instanceName, functions, loggingOn, fmuResourceLocation);

    if (!client)
        return NULL;

    strncpy(client->communication->shm->instance_name, instanceName,
        sizeof(client->communication->shm->instance_name));

    strncpy(client->communication->shm->token, fmuGUID,
        sizeof(client->communication->shm->token));

    strncpy(client->communication->shm->resource_directory, fmuResourceLocation,
        sizeof(client->communication->shm->resource_directory));
    
    fmi2Status status = make_rpc(client, RPC_fmi2Instantiate);

    if ((status != fmi2Warning) && (status != fmi2OK)) {
        client_free(client);
        return NULL;
    }

    return (fmi2Component)client;
}


void fmi2FreeInstance(fmi2Component c) {
    client_t* client = (client_t*)c;

    make_rpc(client, RPC_fmi2FreeInstance);
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

    client->communication->shm->values[0] = toleranceDefined;
    client->communication->shm->values[1] = tolerance;
    client->communication->shm->values[2] = startTime;
    client->communication->shm->values[3] = stopTimeDefined;
    client->communication->shm->values[4] = stopTime;

    return make_rpc(client, RPC_fmi2SetupExperiment);
}


fmi2Status fmi2EnterInitializationMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, RPC_fmi2EnterInitializationMode);
}


fmi2Status fmi2ExitInitializationMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, RPC_fmi2ExitInitializationMode);
}


fmi2Status fmi2Terminate(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, RPC_fmi2Terminate);
}


fmi2Status fmi2Reset(fmi2Component c) {
    client_t* client = (client_t*)c;

    return make_rpc(client, RPC_fmi2Reset);
}


static long int get_pos(fmi2ValueReference vr, const fmi2ValueReference* vr_table, long int offset, unsigned long nb) {
    if (vr == vr_table[offset])
        return offset;

    if (vr == vr_table[offset + nb - 1])
        return offset + nb - 1;

    long int middle = nb / 2;
    if (middle > 0) {
        if (vr > vr_table[offset + middle]) {
            return get_pos(vr, vr_table, offset + middle, nb - middle);
        } else if (vr < vr_table[offset + middle]) {
            return get_pos(vr, vr_table, offset, middle);
        } else {
            return offset + middle;
        }
    } else
        return -1;
}


/* Getting and setting variable values */
fmi2Status fmi2GetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Real value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.reals.vr, 0, client->communication->nb_reals);
        if (index >= 0)
            value[i] = client->data.reals.value[index];
        else {
            LOG_ERROR(client, "Cannot GetReal vr=%lu", vr[i]);
            return fmi2Error;
        }
    }
    return fmi2OK;
}


fmi2Status fmi2GetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Integer value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.integers.vr, 0, client->communication->nb_integers);
        if (index >= 0)
            value[i] = client->data.integers.value[index];
        else {
            LOG_ERROR(client, "Cannot GetInteger vr=%lu", vr[i]);
            return fmi2Error;
        }
    }
    return fmi2OK;
}


fmi2Status fmi2GetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2Boolean value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.booleans.vr, 0, client->communication->nb_booleans);
        if (index >= 0)
            value[i] = client->data.booleans.value[index];
        else {
            LOG_ERROR(client, "Cannot GetBoolean vr=%lu", vr[i]);
            return fmi2Error;
        }
    }
    return fmi2OK;
}


fmi2Status fmi2GetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, fmi2String  value[]) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2SetReal(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Real value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.reals.vr, 0, client->communication->nb_reals);
        
        if (index >= 0) {
            client->data.reals.value[index] = value[i];
            client->data.reals.changed[index] = true;
        } else {
            LOG_ERROR(client, "Cannot SetReal vr=%lu", vr[i]);
            return fmi2Error;
        }
 
    }
    return fmi2OK;
}


fmi2Status fmi2SetInteger(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.integers.vr, 0, client->communication->nb_integers);
        if (index >= 0) {
            client->data.integers.value[index] = value[i];
            client->data.integers.changed[index] = true;
        } else {
            LOG_ERROR(client, "Cannot SetInteger vr=%lu", vr[i]);
            return fmi2Error;
        }
    }
    return fmi2OK;
}


fmi2Status fmi2SetBoolean(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Boolean value[]) {
    client_t* client = (client_t*)c;

    for (size_t i = 0; i < nvr; i += 1) {
        long int index = get_pos(vr[i], client->data.booleans.vr, 0, client->communication->nb_booleans);
        if (index >= 0) {
            client->data.booleans.value[index] = value[i];
            client->data.booleans.changed[index] = true;
        } else {
            LOG_ERROR(client, "Cannot SetBoolean vr=%lu", vr[i]);
            return fmi2Error;
        }
    }
    return fmi2OK;
}


fmi2Status fmi2SetString(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2String  value[]) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/* Getting and setting the internal FMU state */
fmi2Status fmi2GetFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2SetFMUstate(fmi2Component c, fmi2FMUstate  FMUstate) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2FreeFMUstate(fmi2Component c, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2SerializedFMUstateSize(fmi2Component c, fmi2FMUstate  FMUstate, size_t* size) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2SerializeFMUstate(fmi2Component c, fmi2FMUstate  FMUstate, fmi2Byte none[], size_t size) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status  fmi2SetDebugLogging(fmi2Component c,
    fmi2Boolean loggingOn,
    size_t nCategories,
    const fmi2String categories[]) {

    return fmi2OK;
}


fmi2Status fmi2DeSerializeFMUstate(fmi2Component c, const fmi2Byte serializedState[], size_t size, fmi2FMUstate* FMUstate) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/* Getting partial derivatives */
fmi2Status fmi2GetDirectionalDerivative(fmi2Component c, const fmi2ValueReference vUnknown_ref[], size_t nUnknown, const fmi2ValueReference vKnown_ref[], size_t nKnown, const fmi2Real dvKnown[], fmi2Real dvUnknown[]) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/*
 * Types for Functions for FMI2 for Model Exchange
 */

/* Enter and exit the different modes */
fmi2Status fmi2EnterEventMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2NewDiscreteStates(fmi2Component c, fmi2EventInfo* eventInfo) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2EnterContinuousTimeMode(fmi2Component c) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2CompletedIntegratorStep(fmi2Component c,
    fmi2Boolean  noSetFMUStatePriorToCurrentPoint, fmi2Boolean* enterEventMode,
    fmi2Boolean* terminateSimulation) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/* Providing independent variables and re-initialization of caching */
fmi2Status fmi2SetTime(fmi2Component c, fmi2Real time) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2SetContinuousStates(fmi2Component c, const fmi2Real x[], size_t nx) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/* Evaluation of the model equations */
fmi2Status fmi2GetDerivatives(fmi2Component c, fmi2Real derivatives[], size_t nx) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetEventIndicators(fmi2Component c, fmi2Real eventIndicators[], size_t ni) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetContinuousStates(fmi2Component c, fmi2Real x[], size_t nx) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetNominalsOfContinuousStates(fmi2Component c, fmi2Real x_nominal[], size_t nx) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/*
 * Types for Functions for FMI2 for Co-Simulation
 */

/* Simulating the slave */
fmi2Status fmi2SetRealInputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], const fmi2Real value[]) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetRealOutputDerivatives(fmi2Component c, const fmi2ValueReference vr[], size_t nvr, const fmi2Integer order[], fmi2Real value[]) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2DoStep(fmi2Component c, fmi2Real currentCommunicationPoint, fmi2Real communicationStepSize, fmi2Boolean noSetFMUStatePriorToCurrentPoint) {
    client_t* client = (client_t*)c;

    client->communication->shm->values[0] = currentCommunicationPoint;
    client->communication->shm->values[1] = communicationStepSize;
    client->communication->shm->values[2] = noSetFMUStatePriorToCurrentPoint;

    return make_rpc(client, RPC_fmi2DoStep);
}


fmi2Status fmi2CancelStep(fmi2Component c) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


/* Inquire slave status */
fmi2Status fmi2GetStatus(fmi2Component c, const fmi2StatusKind s, fmi2Status* value) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetRealStatus(fmi2Component c, const fmi2StatusKind s, fmi2Real* value) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetIntegerStatus(fmi2Component c, const fmi2StatusKind s, fmi2Integer* value) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetBooleanStatus(fmi2Component c, const fmi2StatusKind s, fmi2Boolean* value) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__
}


fmi2Status fmi2GetStringStatus(fmi2Component c, const fmi2StatusKind s, fmi2String* value) {
    client_t* client = (client_t*)c;

    __NOT_IMPLEMENTED__

}
