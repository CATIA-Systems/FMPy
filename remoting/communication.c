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
#   ifndef HAVE_SEM_TIMEDWAIT
#       include <signal.h>
#   endif
#endif

#define SHM_DEBUG
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


#ifndef HAVE_SEM_TIMEDWAIT
static void communication_alarm_handler(int sig) {
    /* nop */
    return;
}
#endif

static sem_handle_t communication_sem_create(const char *name) {
    sem_handle_t sem;

#ifdef WIN32
    sem = CreateSemaphoreA(NULL, 0, 1, name);
#else
    sem = sem_open(name, O_RDWR | O_CREAT, 0660, 0);
#endif

    return sem;
} 


static void communication_sem_free(sem_handle_t sem) {
    if (sem)
#ifdef WIN32
       CloseHandle(sem);
#else
        sem_close(sem);
#endif

    return;
} 


static void communication_shm_free(shm_handle_t map_file, const char *shm_name) {
#ifdef WIN32
    CloseHandle(map_file);
#else
    shm_unlink(shm_name);
#endif
}


static shm_handle_t communication_shm_create(const char *shm_name, size_t memory_size) {
    shm_handle_t map_file;
 #ifdef WIN32
    map_file = CreateFileMappingA(
        INVALID_HANDLE_VALUE,           // use paging file
        NULL,                           // default security
        PAGE_READWRITE,                 // read/write access
        0,                              // maximum object size (high-order DWORD)
        memory_size,                    // maximum object size (low-order DWORD)
        shm_name);                      // name of mapping object
        
#else
    map_file = shm_open(
        shm_name,
        O_CREAT | O_EXCL | O_RDWR,
        0600);
    ftruncate(map_file, memory_size);
#endif
    SHM_LOG("SHM `%s' create. Notify server.\n", shm_name);
    
    return map_file;
}


static shm_handle_t communication_shm_join(const char *shm_name) {
    shm_handle_t map_file;

#ifdef WIN32
    map_file = OpenFileMapping(
        FILE_MAP_ALL_ACCESS,            // read/write access
        FALSE,                          // do not inherit the name
        shm_name);    // name of mapping object
#else
    map_file = shm_open(
        shm_name,
        O_RDWR,
        0600);
#endif
    SHM_LOG("SHM `%s' joint\n", shm_name);

    return map_file;
}


static void *communication_shm_map(shm_handle_t map_file, size_t memory_size) {
    void *data;
#ifdef WIN32
    data = MapViewOfFile(map_file, FILE_MAP_ALL_ACCESS,
        0, 0, memory_size);
#else
    data = mmap(NULL, memory_size, PROT_READ | PROT_WRITE,
        MAP_SHARED, map_file, 0);
#endif

    return data;
}


static void communication_shm_unmap(void *addr, size_t len) {
#ifdef WIN32
    UnmapViewOfFile(addr);
#else
    munmap(addr, len);
#endif
}


void communication_free(communication_t* communication) {
    free(communication->event_client_name);
    free(communication->event_server_name);
    free(communication->shm_name);

    communication_shm_unmap(communication->data, communication->data_size);
    communication_shm_free(communication->map_file, communication->shm_name);

    communication_sem_free(communication->client_ready);
    communication_sem_free(communication->server_ready);

    free(communication);
}


communication_t *communication_new(const char *prefix, int memory_size, communication_endpoint_t endpoint) {
    communication_t* communication = malloc(sizeof(*communication));
    if (!communication)
        return NULL;

    communication->event_client_name = concat(prefix, "_client");
    communication->event_server_name = concat(prefix, "_server");
    communication->shm_name = concat(prefix, "_memory");

    communication->client_ready = communication_sem_create(communication->event_client_name);
    if (!communication->client_ready) {
        SHM_LOG("*** Cannot CreateSemaphore(%s)\n", communication->event_client_name);
        communication_free(communication);
        return NULL;
    }

    communication->server_ready = communication_sem_create(communication->event_server_name);
    if (!communication->server_ready) {
        SHM_LOG("*** Cannot CreateSemaphore(%s)\n", communication->event_server_name);
        communication_free(communication);
        return NULL;
    }

    communication->data = NULL;
    communication->map_file = SHM_INVALID;

    SHM_LOG("Initialize SHM size=%d\n", memory_size);
    if (endpoint == COMMUNICATION_CLIENT) {
        /* 1st. CLIENT should create memory and notify the client */
        communication->map_file = communication_shm_create(communication->shm_name, memory_size);
        communication_client_ready(communication);
    } else {
        /* 2nd. Server should wait for memory creation by client and connect to it */
        SHM_LOG("Wait for client to initialize SHM.\n");
        communication_waitfor_client(communication);
        communication->map_file = communication_shm_join(communication->shm_name);
        communication_server_ready(communication);
    }

    if (communication->map_file == SHM_INVALID) {
        communication_free(communication);
        SHM_LOG("ERROR: Cannot open or create map file.\n");
        return NULL;
    }

    communication->data = communication_shm_map(communication->map_file, memory_size);
    if (!communication->data) {
        communication_free(communication);
        SHM_LOG("ERROR: Cannot map SHM.\n");
        return NULL;
    }
    communication->data_size = memory_size;

    /* Paranoia: initialize shared memory */
    if (endpoint == COMMUNICATION_CLIENT)
        memset(communication->data, 0, communication->data_size);


#if !defined WIN32 && !defined HAVE_SEM_TIMEDWAIT
    /* Make SIG_ALARM interrupt system call without other side effect */
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

#   endif
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
