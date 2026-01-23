#ifdef WIN32
#   include <windows.h>
#else
#   include <dlfcn.h>
#   include <stdlib.h> 
#   include <signal.h>
#   include <string.h>
#   include <errno.h>
#   include <unistd.h>
#   include <sys/types.h>
#   include <sys/time.h>
#   include <sys/resource.h>
#   include <sys/wait.h>
#endif

#include <fmi2Functions.h> /* for fmi2Instanciate symbol */

#include "communication.h"
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
    PROCESS_INFORMATION pi;

    ZeroMemory(&pi, sizeof(pi));
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);

    ZeroMemory(&handle, sizeof(handle));

    cmd[0] = '\0';
    for (int i = 0; argv[i]; i++) {
        strncat(cmd, argv[i], sizeof(cmd) - strlen(cmd));
        strncat(cmd, " ", sizeof(cmd) - strlen(cmd));
    }
    
    if (CreateProcessA(NULL,            // the path
        cmd,                            // command line
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
    switch(handle = fork()) {
        case -1:
            return -1;
        
        case 0:
            /* CHILD (server) */
            execv(argv[0], argv);
            exit(-1);

        default:
            /* FATHER (client) */
            /* NOP */
            break;
    }
#endif
    return handle; /* Reached only by client */
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
    waitpid(handle, &reason, WNOHANG);
#endif
}
