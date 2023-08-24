#ifdef WIN32
#   include <windows.h>
#else
#   include <stdlib.h> 
#   include <signal.h>
#   define _GNU_SOURCE  /* to access to dladdr */
#   include <dlfcn.h>
#   include <string.h>
#   include <unistd.h>
#endif

#include "process.h"


int process_is_alive(process_handle_t handle) {
#ifdef WIN32
    return WaitForSingleObject(handle, 0) == WAIT_TIMEOUT;
#else
    return ! kill(handle, 0);
#endif
}

int process_module_path(char path[MAX_PATH])  {
#ifdef WIN32
    HMODULE hm = NULL;

    if (GetModuleHandleEx(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS |
        GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        (LPCSTR)&process_module_path, &hm) == 0) {
            return -1;
    }
    if (GetModuleFileName(hm, path, MAX_PATH) == 0) {
            return -2;
    }
#else
    Dl_info info;
    if (dladdr(process_module_path, &info))
        return -1;
    strncpy(path, info.dli_fname, MAX_PATH);
#endif
    return 0;
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
            return -1;
        case 0:     /* child */
            execv(argv[0], argv);
            exit(-1);
        default:    /* father */
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
    wait4(handle, &reason,WNOHANG, NULL);
#endif
}
