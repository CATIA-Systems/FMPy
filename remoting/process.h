/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifndef PROCESS_H
#define PROCESS_H


/*-----------------------------------------------------------------------------
                    P R O C E S S _ H A N D L E _ T
-----------------------------------------------------------------------------*/
#ifdef WIN32
#include <windows.h>
typedef HANDLE process_handle_t;
#else
#include <unistd.h>
typedef pid_t process_handle_t;
#endif

#ifndef MAX_PATH
#   define MAX_PATH 4096
#endif

/*-----------------------------------------------------------------------------
                               P R O T O T Y P E S
-----------------------------------------------------------------------------*/

extern int process_is_alive(process_handle_t handle);
extern process_handle_t process_spawn(char *const argv[]);
extern unsigned long int process_current_id(void);
extern void process_close_handle(process_handle_t handle);
void process_waitfor(process_handle_t handle);

#endif
