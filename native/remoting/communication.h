#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#include <stdbool.h>

#ifdef WIN32
#	include <windows.h>
#else
#	include <fcntl.h>
#	include <sys/mman.h>
#endif

#include <fmi2Functions.h>

/*-----------------------------------------------------------------------------
             C O M M U N I C A T I O N _ E N D P O I N T _ T
-----------------------------------------------------------------------------*/

typedef enum {
	COMMUNICATION_CLIENT=1,
	COMMUNICATION_SERVER=5
} communication_endpoint_t;


/*-----------------------------------------------------------------------------
                             S H M _ H A N D L E _ T
-----------------------------------------------------------------------------*/
#ifdef WIN32
typedef HANDLE shm_handle_t;
#	define SHM_INVALID	NULL
#else
typedef int shm_handle_t;
#	define SHM_INVALID	-1
#endif


/*-----------------------------------------------------------------------------
                             S E M _ H A N D L E _ T
-----------------------------------------------------------------------------*/
#ifdef WIN32
typedef HANDLE sem_handle_t;
#	define SEM_INVALID	NULL
#else
typedef int sem_handle_t;
#	define SEM_INVALID	-1
#endif

/*
*/
typedef enum {
	RPC_fmi2Instantiate=1,
	RPC_fmi2FreeInstance=2,
	RPC_fmi2SetupExperiment=3,
	RPC_fmi2EnterInitializationMode=4,
	RPC_fmi2ExitInitializationMode=5,
	RPC_fmi2Terminate=6,
	RPC_fmi2Reset=7,
	RPC_fmi2DoStep=8,
} rpc_function_t;

typedef struct {
    fmi2Real                *value;
    fmi2ValueReference      *vr;
	bool					*changed;
} communication_data_reals_t;

typedef struct {
    fmi2Integer             *value;
    fmi2ValueReference      *vr;
	bool					*changed;
} communication_data_integers_t;

typedef struct {
    fmi2Boolean             *value;
    fmi2ValueReference      *vr;
	bool					*changed;
} communication_data_booleans_t;

typedef struct {
	communication_data_reals_t		reals;
	communication_data_integers_t	integers;
	communication_data_booleans_t	booleans;
} communication_data_t;

/*
*/
#define COMMUNICATION_MESSAGE_SIZE	4096
typedef struct {
    fmi2Status          status;
    rpc_function_t   	function;
	char				message[COMMUNICATION_MESSAGE_SIZE];
    double              values[5];
    char                instance_name[128];
    char                token[128];
    char                resource_directory[4096];
} communication_shm_t;

/*-----------------------------------------------------------------------------
                         C O M M U N I C A T I O N _ T
-----------------------------------------------------------------------------*/
#define COMMUNICATION_KEY_LEN         16
#define COMMUNICATION_TIMEOUT_DEFAULT 3000
typedef struct {
	communication_endpoint_t	endpoint;
	char						*sem_name_client;
	char						*sem_name_server;
	char						*shm_name;
	shm_handle_t				map_file;
	sem_handle_t				client_ready;
	sem_handle_t				server_ready;
	size_t						data_size;
	unsigned long  				nb_reals;
	unsigned long      	        nb_integers;
	unsigned long          		nb_booleans;
    communication_shm_t         *shm;
} communication_t;


/*-----------------------------------------------------------------------------
                               P R O T O T Y P E S
-----------------------------------------------------------------------------*/

extern void communication_free(communication_t* communication);
extern communication_t *communication_new(const char *prefix, unsigned long nb_reals,
	unsigned long nb_integers, unsigned long nb_booleans, communication_endpoint_t endpoint);
extern void communication_data_initialize(communication_data_t *data, communication_t *communication);
extern void communication_client_ready(const communication_t* communication);
extern void communication_waitfor_server(const communication_t* communication);
extern int communication_timedwaitfor_server(const communication_t* communication, int timeout);
extern void communication_waitfor_client(const communication_t* communication);
extern int communication_timedwaitfor_client(const communication_t* communication, int timeout);
extern void communication_server_ready(const communication_t* communication);

#endif
