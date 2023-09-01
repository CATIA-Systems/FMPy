/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */
#include "config.h"

#include <stdlib.h>
#include <string.h>
#ifndef WIN32
#   include <errno.h>
#   include <unistd.h>
#   include <sys/time.h>
#   ifdef __APPLE__
#       include <signal.h>
#   endif
#endif

//#define SHM_DEBUG
#ifdef SHM_DEBUG
#   include <stdio.h>
#   define SHM_LOG(message, ...) printf("[SHM] " message, ##__VA_ARGS__)
#else
#   define SHM_LOG(message, ...)
#endif

#include "communication.h"


static char* concat(const char* prefix, const char* name) {
    char* string = malloc(strlen(prefix) + strlen(name) + 1);
    if (string) {
        strcpy(string, prefix);
        strcat(string, name);
    }
    return string;
}

void communication_free(communication_t* communication) {
    free(communication->event_client_name);
    free(communication->event_server_name);
    free(communication->memory_name);

    if (communication->data)
#ifdef WIN32
        UnmapViewOfFile(communication->data);
#else
        munmap(communication->data, communication->data_size);
#endif
    communication->data = NULL;

    if (communication->map_file)
#ifdef WIN32
        CloseHandle(communication->map_file);
#else
        shm_unlink(communication->memory_name);
#endif

    if (communication->client_ready)
#ifdef WIN32
        CloseHandle(communication->client_ready);
#else
        sem_close(communication->client_ready);
#endif

    if (communication->server_ready)
#ifdef WIN32
        CloseHandle(communication->server_ready);
#else
        sem_close(communication->server_ready);
#endif

    free(communication);
}


#ifndef HAVE_SEM_TIMEDWAIT
static void communication_alarm_handler(int sig) {
    return;
}
#endif

communication_t *communication_new(const char *prefix, int memory_size, communication_endpoint_t endpoint) {
    communication_t* communication = malloc(sizeof(*communication));
    if (!communication)
        return NULL;

    communication->event_client_name = concat(prefix, "_client");
    communication->event_server_name = concat(prefix, "_server");
    communication->memory_name = concat(prefix, "_memory");

#ifdef WIN32
    communication->client_ready = CreateSemaphoreA(NULL, 0, 1, communication->event_client_name);
#else
    communication->client_ready = sem_open(communication->event_client_name, O_RDWR | O_CREAT);
#endif
    if (!communication->client_ready) {
        SHM_LOG("*** Cannot CreateSemaphore(%s)\n", communication->event_client_name);
        communication_free(communication);
        return NULL;
    }
    
#ifdef WIN32
    communication->server_ready = CreateSemaphoreA(NULL, 0, 1, communication->event_server_name);
#else
    communication->server_ready = sem_open(communication->event_server_name, O_RDWR | O_CREAT);
#endif
    if (!communication->server_ready) {
        SHM_LOG("*** Cannot CreateSemaphore(%s)\n", communication->event_server_name);
        communication_free(communication);
        return NULL;
    }

    communication->data = NULL;
    communication->map_file = SHM_INVALID;

    SHM_LOG("Initialize SHM size=%d\n", memory_size);
    if (endpoint == COMMUNICATION_CLIENT) {
        /* Server should create memory and notify the client */
 #ifdef WIN32
        communication->map_file = CreateFileMappingA(
            INVALID_HANDLE_VALUE,           // use paging file
            NULL,                           // default security
            PAGE_READWRITE,                 // read/write access
            0,                              // maximum object size (high-order DWORD)
            memory_size,                    // maximum object size (low-order DWORD)
            communication->memory_name);    // name of mapping object
        SHM_LOG("SHM `%s' create. Notify server.\n", communication->memory_name);
#else
        communication->map_file = shm_open(
            communication->memory_name,
            O_CREAT | O_EXCL | O_RDWR,
            0600);
        ftruncate(communication->map_file, memory_size);
#endif
        communication_client_ready(communication);
    } else {
        /* Server should wait for memory creation by client and connect to it */
        SHM_LOG("Wait for client to initialize SHM.\n");
        communication_waitfor_client(communication);
#ifdef WIN32
        communication->map_file = OpenFileMapping(
            FILE_MAP_ALL_ACCESS,            // read/write access
            FALSE,                          // do not inherit the name
            communication->memory_name);    // name of mapping object
#else
        communication->map_file = shm_open(
            communication->memory_name,
            O_RDWR,
            0600);
#endif
        SHM_LOG("SHM `%s' joint.\n", communication->memory_name);
        communication_server_ready(communication);
    }

    if (communication->map_file == SHM_INVALID) {
        communication_free(communication);
        SHM_LOG("ERROR: Cannot open or create map file.\n");
        return NULL;
    }

#ifdef WIN32
    communication->data = MapViewOfFile(communication->map_file, FILE_MAP_ALL_ACCESS,
        0, 0, memory_size);
#else
    communication->data = mmap(NULL, memory_size, PROT_READ | PROT_WRITE,
                           MAP_SHARED, communication->map_file, 0);
#endif
    if (!communication->data) {
        communication_free(communication);
        SHM_LOG("ERROR: Cannot map SHM.\n");
        return NULL;
    }
    communication->data_size = memory_size;


#ifndef HAVE_SEM_TIMEDWAIT
    /* Make SIG_ALARM interrupt system call */
    struct sigaction sa;
    sa.sa_handler = communication_alarm_handler;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;
    sigaction(SIGALRM, &sa, NULL);
#endif

    return communication;
}


void communication_client_ready(const communication_t* communication) {
#ifdef WIN32
    ReleaseSemaphore(communication->client_ready, 1, NULL);
#else
    sem_post(communication->client_ready);
#endif

    return;
}


void communication_waitfor_server(const communication_t* communication) {
#ifdef WIN32
    WaitForSingleObject(communication->server_ready, INFINITE);
#else
    sem_wait(communication->server_ready);
#endif
    return;
}


int communication_timedwaitfor_server(const communication_t* communication, int timeout) {
#ifdef WIN32
    return WaitForSingleObject(communication->server_ready, timeout) == WAIT_TIMEOUT;
#else
#   ifdef HAVE_SEM_TIMEDWAIT
    struct timespec ts;

    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec  += timeout / 1000;
    ts.tv_nsec += (timeout - ts.tv_sec * 1000) * 1000000;
    if (sem_timedwait(communication->client_ready, &ts) < 0)
        return errno == ETIMEDOUT;
    return 0;

#   else
    struct itimerval value, old_value;

    value.it_interval.tv_sec = 0;
    value.it_interval.tv_usec = 0;
    value.it_value.tv_sec = timeout / 1000;
    value.it_value.tv_usec = (timeout - value.it_value.tv_sec * 1000) * 1000;

    setitimer(ITIMER_REAL, &value, &old_value);
    int status = sem_wait(communication->server_ready);
    setitimer(ITIMER_REAL, &old_value, NULL);
    
    if (status < 0)
        return errno == EINTR;
    
    return 0;
#   endif
#endif
}


void communication_waitfor_client(const communication_t* communication) {
#ifdef WIN32
    WaitForSingleObject(communication->client_ready, INFINITE);
#else
    sem_wait(communication->client_ready);
#endif
    return;
}


int communication_timedwaitfor_client(const communication_t* communication, int timeout) {
#ifdef WIN32
    return WaitForSingleObject(communication->client_ready, timeout) == WAIT_TIMEOUT;
#else
#   ifdef HAVE_SEM_TIMEDWAIT
    struct timespec ts;

    clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec  += timeout / 1000;
    ts.tv_nsec += (timeout - ts.tv_sec * 1000) * 1000000;
    if (sem_timedwait(communication->client_ready, &ts) < 0)
        return errno == ETIMEDOUT;
    return 0;

#   else
    struct itimerval value, old_value;

    value.it_interval.tv_sec = 0;
    value.it_interval.tv_usec = 0;
    value.it_value.tv_sec = timeout / 1000;
    value.it_value.tv_usec = (timeout - value.it_value.tv_sec * 1000) * 1000;

    setitimer(ITIMER_REAL, &value, &old_value);
    int status = sem_wait(communication->client_ready);
    setitimer(ITIMER_REAL, &old_value, NULL);
    
    if (status < 0)
        return errno == EINTR;
    
    return 0;

#endif
    return 0;
#endif
}


void communication_server_ready(const communication_t* communication) {
#ifdef WIN32
    ReleaseSemaphore(communication->server_ready, 1, NULL);
#else
    sem_post(communication->server_ready);
#endif

    return;
}
