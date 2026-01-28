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
#include "server.h"

//#define SERVER_DEBUG 1
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
        char *const log_buffer = server->communication->shm->message;
        size_t offset = strlen(log_buffer);
        
        va_start(params, message);
        vsnprintf(log_buffer + offset, COMMUNICATION_MESSAGE_SIZE - offset, message, params);
        va_end(params);

        offset = strlen(log_buffer);
        if (offset < COMMUNICATION_MESSAGE_SIZE-1) {
            log_buffer[offset] = '\n';
            log_buffer[offset+1] = '\0';
        }
        log_buffer[COMMUNICATION_MESSAGE_SIZE-1] = '\0'; /* paranoia */
        
        SERVER_LOG("LOG: %s\n", log_buffer + offset);
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


static int map_entries(fmu_entries_t* entries, library_t library) {
#	define MAP(x) entries->x = (x ## TYPE*)library_symbol(library, #x); \
	SERVER_LOG("function %-30s: %s\n", "`" #x "'", (entries->x)?"found":"not implemented"); \
    if (! entries->x) return -1;

    MAP(fmi2Instantiate);
    MAP(fmi2FreeInstance);
    MAP(fmi2SetupExperiment);
    MAP(fmi2EnterInitializationMode);
    MAP(fmi2ExitInitializationMode);
    MAP(fmi2Terminate);
    MAP(fmi2Reset);
    MAP(fmi2GetReal);
    MAP(fmi2GetInteger);
    MAP(fmi2GetBoolean);
    MAP(fmi2SetReal);
    MAP(fmi2SetInteger);
    MAP(fmi2SetBoolean);
    MAP(fmi2DoStep);
#undef MAP
    return 0;
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
    free(server->update.reals.value);
    free(server->update.reals.vr);
    free(server->update.integers.value);
    free(server->update.integers.vr);
    free(server->update.booleans.value);
    free(server->update.booleans.vr);
    free(server);

    return;
}
    

static server_t* server_new(const char *library_filename, unsigned long ppid, const char *secret,
    unsigned long nb_reals, unsigned long nb_integers, unsigned long nb_booleans) {
    server_t* server;
    server = malloc(sizeof(*server));
    if (!server)
        return NULL;
    server->instance_name = NULL;
    server->component = NULL;
    server->is_debug = 0;
    server->update.reals.value = NULL;
    server->update.reals.vr = NULL;
    server->update.integers.value = NULL;
    server->update.integers.vr = NULL;
    server->update.booleans.value = NULL;
    server->update.booleans.vr = NULL;
    server->communication = NULL;
    server->library = NULL;

#define ALLOC(nb, ptr) \
    if (nb) { \
        ptr = malloc(sizeof(*ptr) * nb); \
        if (!ptr) { \
            server_free(server); \
            return NULL; \
        } \
    } else { \
        ptr = NULL; \
    }

    ALLOC(nb_reals, server->update.reals.value);
    ALLOC(nb_reals, server->update.reals.vr);
    ALLOC(nb_integers, server->update.integers.value);
    ALLOC(nb_integers, server->update.integers.vr);
    ALLOC(nb_booleans, server->update.booleans.value);
    ALLOC(nb_booleans, server->update.booleans.vr);

#undef ALLOC

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

    server->communication = communication_new(server->shared_key, nb_reals, nb_integers, nb_booleans, COMMUNICATION_SERVER);
    communication_data_initialize(&server->data, server->communication);

    /* At this point Client and Server are Synchronized */

    return server;
}


/*-----------------------------------------------------------------------------
                             M A I N   L O O P
-----------------------------------------------------------------------------*/

static int is_parent_still_alive(const server_t *server) {
    return process_is_alive(server->parent_handle);
}

static fmi2Status setup_experiment(const server_t* server) {
    fmi2Boolean toleranceDefined = (int)server->communication->shm->values[0];
    fmi2Real tolerance = server->communication->shm->values[1];
    fmi2Real startTime = server->communication->shm->values[2];
    fmi2Boolean stopTimeDefined = (int)server->communication->shm->values[3];
    fmi2Real stopTime = server->communication->shm->values[4];

    return server->entries.fmi2SetupExperiment(
        server->component,
        toleranceDefined,
        tolerance,
        startTime,
        stopTimeDefined,
        stopTime);
}


static fmi2Status update_values_from_client(server_t* server) {
    fmi2Status status = fmi2OK;

    unsigned long nb_reals = 0;
    for (unsigned long i = 0; i < server->communication->nb_reals; i += 1) {
        if (server->data.reals.changed[i]) {
            server->update.reals.vr[nb_reals] = server->data.reals.vr[i];
            server->update.reals.value[nb_reals] = server->data.reals.value[i];
            nb_reals += 1;
            server->data.reals.changed[i] = false;
        }
    }
    if (nb_reals) {
        status = server->entries.fmi2SetReal(server->component, server->update.reals.vr,
            nb_reals, server->update.reals.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot apply REALS buffer.");
            return status;
        }
    }

    unsigned long nb_integers = 0;
    for (unsigned long i = 0; i < server->communication->nb_integers; i += 1) {
        if (server->data.integers.changed[i]) {
            server->update.integers.vr[nb_integers] = server->data.integers.vr[i];
            server->update.integers.value[nb_integers] = server->data.integers.value[i];
            nb_integers += 1;
            server->data.integers.changed[i] = false;
        }
    }
    if (nb_integers) {
        status = server->entries.fmi2SetInteger(server->component, server->update.integers.vr,
            nb_integers, server->update.integers.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot apply INTEGERS buffer.");
            return status;
        }
    }

    unsigned long nb_booleans = 0;
    for (unsigned long i = 0; i < server->communication->nb_booleans; i += 1) {
        if (server->data.booleans.changed[i]) {
            server->update.booleans.vr[nb_booleans] = server->data.booleans.vr[i];
            server->update.booleans.value[nb_booleans] = server->data.booleans.value[i];
            nb_booleans += 1;
            server->data.booleans.changed[i] = false;
        }
    }
    if (nb_booleans) {
        status = server->entries.fmi2SetBoolean(server->component, server->update.booleans.vr,
            nb_booleans, server->update.booleans.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot apply BOOLEANS buffer.");
            return status;
        }
    }

    return status;
}


static fmi2Status update_buffer_from_values(server_t* server) {
    fmi2Status status = fmi2OK;

    status = server->entries.fmi2GetReal(server->component, server->data.reals.vr,
        server->communication->nb_reals, server->data.reals.value);
    if (status != fmi2OK) {
        LOG_ERROR(server, "Cannot initialize REALS buffer.");
        return status;
    }

    status = server->entries.fmi2GetInteger(server->component, server->data.integers.vr,
        server->communication->nb_integers, server->data.integers.value);
    if (status != fmi2OK) {
        LOG_ERROR(server, "Cannot initialize INTEGERS buffers.");
        return status;
    }

    status = server->entries.fmi2GetBoolean(server->component, server->data.booleans.vr,
        server->communication->nb_booleans, server->data.booleans.value);
    if (status != fmi2OK) {
        LOG_ERROR(server, "Cannot initialize BOOLEANS buffers");
        return status;
    }

    return status;
}


static fmi2Status instanciate(server_t* server) {
    server->instance_name = strdup(server->communication->shm->instance_name);
    server->is_debug = fmi2False;
    server->library = library_load(server->library_filename);
    if (!server->library) {
        LOG_ERROR(server, "Cannot open DLL object '%s'. ", server->library_filename);
        return fmi2Error;
    }
    if (map_entries(&server->entries, server->library) < 0)
        return fmi2Error;

    server->component = server->entries.fmi2Instantiate(
        server->communication->shm->instance_name,
        fmi2CoSimulation,
        server->communication->shm->token,
        server->communication->shm->resource_directory,
        &server->functions,
        fmi2False,
        fmi2False);

    if (!server->component) {
        LOG_ERROR(server, "Cannot instanciate FMU.");
        return fmi2Error;
    }

    return fmi2OK;
}


static fmi2Status free_instance(server_t *server) {
    server->entries.fmi2FreeInstance(server->component);
    server->component = NULL;
    library_unload(server->library);
    server->library = NULL;

    return fmi2OK;
}


static fmi2Status do_step(server_t *server) {
    fmi2Real currentCommunicationPoint = server->communication->shm->values[0];
    fmi2Real communicationStepSize = server->communication->shm->values[1];
    fmi2Boolean noSetFMUStatePriorToCurrentPoint = (int)server->communication->shm->values[2];
    fmi2Status status;
    
    status = update_values_from_client(server);
    if (status != fmi2OK) {
        return status;
    }

    status = server->entries.fmi2DoStep(
        server->component,
        currentCommunicationPoint,
        communicationStepSize,
        noSetFMUStatePriorToCurrentPoint);
    if (status != fmi2OK) {
        LOG_ERROR(server, "Cannot doStep.");
        return status;
    }


    if (server->communication->nb_reals) {
        status = server->entries.fmi2GetReal(server->component, server->data.reals.vr,
            server->communication->nb_reals, server->data.reals.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot update REALS buffer.");
            return status;
        }
    }

    if (server->communication->nb_integers) {
        status = server->entries.fmi2GetInteger(server->component, server->data.integers.vr,
            server->communication->nb_integers, server->data.integers.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot update INTEGERS buffer.");
            return status;
        }
    }

    if (server->communication->nb_booleans) {
        status = server->entries.fmi2GetBoolean(server->component, server->data.booleans.vr,
            server->communication->nb_booleans, server->data.booleans.value);
        if (status != fmi2OK) {
            LOG_ERROR(server, "Cannot update BOOLEANS buffer.");
            return status;
        }
    }

    return fmi2OK;;
}

static fmi2Status initialize(server_t* server) {
    fmi2Status status = fmi2OK;

    status = server->entries.fmi2EnterInitializationMode(server->component);
    if (status != fmi2OK) {
        return status;
    }

    status = update_values_from_client(server);
    if (status != fmi2OK) {
        return status;
    }
    
    status = update_buffer_from_values(server);
    if (status != fmi2OK) {
        return status;
    }

    return status;
}


int main(int argc, char* argv[]) {
    SERVER_LOG("STARING...\n");
    if (argc != 7) {
        fprintf(stderr, "Usage: server <parent_process_id> <secret> <library_path> <nb_reals> <nb_integer> <nb_booleans>\n");
        return 1;
    }

    SERVER_LOG("Initializing...\n");
    server_t* server = server_new(argv[3], strtoul(argv[1], NULL, 10), argv[2], 
        strtoul(argv[4], NULL, 10),
        strtoul(argv[5], NULL, 10),
        strtoul(argv[6], NULL, 10));
    if (!server) {
        SERVER_LOG("Initialize server. Exit.\n");
        return -1;
    }


    communication_shm_t *fmu = server->communication->shm;
    communication_server_ready(server->communication);

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
        rpc_function_t function = fmu->function;
        SERVER_LOG("RPC: %d | execute\n", function);
        fmu->status = -1; /* means that real function is not (yet?) called */

        switch (function) {
        case RPC_fmi2Instantiate:
            fmu->status = instanciate(server);
            break;

        case RPC_fmi2FreeInstance:
            fmu->status = free_instance(server);
            wait_for_function = 0;
            break;

        case RPC_fmi2SetupExperiment:
            fmu->status = setup_experiment(server);
            break;

        case RPC_fmi2EnterInitializationMode:
            fmu->status = initialize(server);
            break;

        case RPC_fmi2ExitInitializationMode:
            fmu->status = server->entries.fmi2ExitInitializationMode(server->component);
            break;

        case RPC_fmi2Terminate:
            fmu->status = server->entries.fmi2Terminate(server->component);
            break;

        case RPC_fmi2Reset:
            fmu->status = server->entries.fmi2Reset(server->component);
            break;

        case RPC_fmi2DoStep:
            fmu->status = do_step(server);
            break;
        }

        /*
         * Acknoledge the client side !
         */
        if (fmu->status < 0) {
            LOG_ERROR(server, "Function '%d' unreachable.", function);
            fmu->status = fmi2Error;
        }
        SERVER_LOG("RPC: %d | processed.\n", function);
        communication_server_ready(server->communication);
    }

    /*
     * End of loop
     */
    server_free(server);
    SERVER_LOG("Exit.\n");

    return 0;
}
