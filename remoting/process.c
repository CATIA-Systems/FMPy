/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifdef WIN32
#   include <windows.h>
#else
#   define _GNU_SOURCE  /* to access to dladdr */
#   include <dlfcn.h>
#   include <stdio.h>
#   include <stdlib.h> 
#   include <signal.h>
#   include <string.h>
#   include <errno.h>
#   include <unistd.h>
#   define _BSD_SOURCE  /* to access wait4 */
#   include <sys/types.h>
#   include <sys/time.h>
#   include <sys/resource.h>
#   include <sys/wait.h>
#endif

#include <fmi2Functions.h> /* for fmi2Instanciate symbol */

#include "process.h"


int process_is_alive(process_handle_t handle) {
#ifdef WIN32
    return WaitForSingleObject(handle, 0) == WAIT_TIMEOUT;
#else
    return ! kill(handle, 0);
#endif
}


process_handle_t process_spawn(char *const argv[])  {
    process_handle_t handle;
#ifdef WIN32
    char cmd[MAX_PATH];
    STARTUPINFO si;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);

    ZeroMemory(&handle, sizeof(handle));

    cmd[0] = '\0';
    for (int i = 0; argv[i]; i++) {
        strncat(cmd, argv[i], sizeof(cmd) - strlen(cmd));
        strncat(cmd, " ", sizeof(cmd) - strlen(cmd));
    }
    PROCESS_INFORMATION pi;
    if (CreateProcessA(NULL,            // the path
        (LPSTR)cmd,                     // command line
        NULL,                           // process handle not inheritable
        NULL,                           // thread handle not inheritable
        FALSE,                          // set handle inheritance to FALSE
        0,                              // creation flags
        NULL,                           // use parent's environment block
        NULL,                           // use parent's starting directory 
        &si,                            // pointer to STARTUPINFO structure
        &pi                             // pointer to PROCESS_INFORMATION structure
    )) {
        CloseHandle(pi.hThread);
        handle = pi.hProcess;
    }
#else
    handle = fork();
    switch(handle) {
        case -1:    /* error */
            printf("FORK() FAILED: errno=%d\n", errno);
            return -1;
        case 0:     /* child */
            execv(argv[0], argv);
            printf("EXECV ERROR: Cannot launch '%s': errno=%d", argv[0], errno);
            exit(-1);
        default:    /* father */
            printf("FORK() OK\n");
            signal(SIGCHLD, SIG_IGN);
    }
#endif
    return handle;
}


unsigned long int process_current_id(void) {
#ifdef WIN32
    return GetCurrentProcessId();
#else
    return getpid();
#endif
}


void process_close_handle(process_handle_t handle) {
#ifdef WIN32
    CloseHandle(handle);
#else
    (void)handle;
#endif
}

void process_waitfor(process_handle_t handle) {
#ifdef WIN32
    WaitForSingleObject(handle, INFINITE);
#else
    int reason; 
    wait4(handle, &reason, WNOHANG, NULL);
#endif
}
