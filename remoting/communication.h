/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#ifdef WIN32
#	include <windows.h>
#else
#	include <fcntl.h>
#	include <sys/mman.h>
#endif

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
	void						*data;
} communication_t;


/*-----------------------------------------------------------------------------
                               P R O T O T Y P E S
-----------------------------------------------------------------------------*/

extern void communication_free(communication_t* communication);
extern communication_t *communication_new(const char *prefix, size_t memory_size, communication_endpoint_t endpoint);
extern void communication_client_ready(const communication_t* communication);
extern void communication_waitfor_server(const communication_t* communication);
extern int communication_timedwaitfor_server(const communication_t* communication, int timeout);
extern void communication_waitfor_client(const communication_t* communication);
extern int communication_timedwaitfor_client(const communication_t* communication, int timeout);
extern void communication_server_ready(const communication_t* communication);

#endif
