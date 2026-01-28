#ifndef CLIENT_H
#define CLIENT_H

#include "communication.h"
#include "process.h"

/*-----------------------------------------------------------------------------
                               C L I E N T _ T
-----------------------------------------------------------------------------*/

typedef struct {
	fmi2ComponentEnvironment	environment;
	const fmi2CallbackFunctions	*functions;
	fmi2CallbackLogger			logger;
	char						*instance_name;
	int							is_debug;
	communication_t				*communication;
	process_handle_t			server_handle;
	char						shared_key[COMMUNICATION_KEY_LEN];
	communication_data_t		data;
} client_t;

#endif
