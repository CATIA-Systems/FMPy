/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifndef CLIENT_H
#define CLIENT_H

#include "communication.h"
#include "process.h"
#include "remote.h"

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
} client_t;

#endif
