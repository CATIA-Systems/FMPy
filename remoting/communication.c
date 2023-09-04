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
#   include <stdio.h>
#   include <unistd.h>
#   ifndef HAVE_SEMTIMEDOP
#       include <signal.h>
#   endif
#   include <sys/time.h>
#   include <sys/sem.h>
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


#if !defined WIN32 && !defined HAVE_SEMTIMEDOP
static void communication_alarm_handler(int sig) {
    /* nop */
    return;
}
#endif


static sem_handle_t communication_sem_open(const char *name, communication_endpoint_t endpoint) {
    sem_handle_t sem;

#ifdef WIN32
    sem = CreateSemaphoreA(NULL, init, 1, name);
#else
    SHM_LOG("Create SEM %s from=%d\n", name, endpoint);
    int flags = 0600;
    if (endpoint == COMMUNICATION_CLIENT) {
        flags |=  IPC_CREAT | IPC_EXCL;
        FILE *sem_file = fopen(name, "w");
        if (!sem_file) 
            return SEM_INVALID;
       fclose(sem_file);
    }
    sem = semget(ftok(name, 0), 1, flags);
#endif

    return sem;
}


static void communication_sem_free(sem_handle_t sem, const char *sem_name) {
    if (sem)
#ifdef WIN32
       CloseHandle(sem);
#else
        SHM_LOG("communication_sem_free(%s)\n", sem_name);
        if (semctl(sem, 0, IPC_RMID)<0) {
            perror("semctl");
        }
        if (unlink(sem_name) < 0) {
            perror("unlink");
        }
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

    communication_shm_unmap(communication->data, communication->data_size);
    communication_shm_free(communication->map_file, communication->shm_name);

    communication_sem_free(communication->server_ready, communication->event_server_name);
    communication_sem_free(communication->client_ready, communication->event_client_name);

    free(communication->event_client_name);
    free(communication->event_server_name);
    free(communication->shm_name);

    free(communication);
}


communication_t *communication_new(const char *prefix, int memory_size, communication_endpoint_t endpoint) {
    communication_t* communication = malloc(sizeof(*communication));
    if (!communication)
        return NULL;

    communication->endpoint = endpoint;
#ifdef WIN32
    communication->event_client_name = concat(prefix, "_client");
    communication->event_server_name = concat(prefix, "_server");
#else
    /* on Unix, semaphores require an existing file
       it will be created in following function */
    char *tmp_prefix = concat("/tmp", prefix);
    communication->event_client_name = concat(tmp_prefix, "_client");
    communication->event_server_name = concat(tmp_prefix, "_server");
    free(tmp_prefix);
#endif

    communication->shm_name = concat(prefix, "_memory");

    communication->client_ready = communication_sem_open(communication->event_client_name, endpoint);
    if (communication->client_ready == SEM_INVALID) {
        SHM_LOG("Cannot CreateSemaphore(%s): %s\n", communication->event_client_name, strerror(errno));
        communication_free(communication);
        return NULL;
    }

    communication->server_ready = communication_sem_open(communication->event_server_name, endpoint);
    if (communication->server_ready == SEM_INVALID) {
        SHM_LOG("Cannot CreateSemaphore(%s): %s\n", communication->event_server_name, strerror(errno));
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
        SHM_LOG("Client ready. Joining SHM\n");
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


    #if !defined WIN32 && !defined HAVE_SEMTIMEDOP
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
    SHM_LOG("communication_client_ready()\n");
    struct sembuf up = {0,1,0};
    semop(communication->client_ready, &up, 1);
#endif
    return;
}


void communication_waitfor_server(const communication_t* communication) {
#ifdef WIN32
    WaitForSingleObject(communication->server_ready, INFINITE);
#else
    SHM_LOG("communication_waitfor_server()\n");
    struct sembuf down = {0,-1,0};
    semop(communication->server_ready, &down, 1);
    SHM_LOG("communication_waitfor_server() --OK\n");
#endif
    return;
}


int communication_timedwaitfor_server(const communication_t* communication, int timeout) {
#ifdef WIN32
    return WaitForSingleObject(communication->server_ready, timeout) == WAIT_TIMEOUT;
#else
    SHM_LOG("communication_timedwaitfor_server(%d)\n", timeout);
    struct sembuf down = {0,-1,0};
#   ifdef HAVE_SEMTIMEDOP
    const struct timespec timeout;
    int status = semtimedop(communication->server_ready, &down, 1, &timeout);
        SHM_LOG("communication_timedwaitfor_server() --DONE\n");
    if (status<0) {
        if (errno == EAGAIN)
            return 1;
        else
            return -1;
    }
    return 0;
#   else
    struct itimerval value, old_value;

    value.it_interval.tv_sec = 0;
    value.it_interval.tv_usec = 0;
    value.it_value.tv_sec = timeout / 1000;
    value.it_value.tv_usec = (timeout - value.it_value.tv_sec * 1000) * 1000;

    setitimer(ITIMER_REAL, &value, &old_value);
    int status = semop(communication->server_ready, &down, 1);
    SHM_LOG("communication_timedwaitfor_server() --DONE\n");
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
    SHM_LOG("communication_waitfor_client()\n");
    struct sembuf down = {0,-1,0};
    semop(communication->client_ready, &down, 1);
    SHM_LOG("communication_waitfor_client() --OK\n");
#endif
    return;
}


int communication_timedwaitfor_client(const communication_t* communication, int timeout) {
#ifdef WIN32
    return WaitForSingleObject(communication->client_ready, timeout) == WAIT_TIMEOUT;
#else
    SHM_LOG("communication_timedwaitfor_client(%d)\n", timeout);
    struct sembuf down = {0,-1,0};
#   ifdef HAVE_SEMTIMEDOP
    const struct timespec timeout;
    int status = semtimedop(communication->client_ready, &down, 1, &timeout);
        SHM_LOG("communication_timedwaitfor_client() --DONE\n");
    if (status<0) {
        if (errno == EAGAIN)
            return 1;
        else
            return -1;
    }
    return 0;
#   else
    struct itimerval value, old_value;

    value.it_interval.tv_sec = 0;
    value.it_interval.tv_usec = 0;
    value.it_value.tv_sec = timeout / 1000;
    value.it_value.tv_usec = (timeout - value.it_value.tv_sec * 1000) * 1000;

    setitimer(ITIMER_REAL, &value, &old_value);
    int status = semop(communication->client_ready, &down, 1);
    SHM_LOG("communication_timedwaitfor_client() --DONE\n");
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
    SHM_LOG("communication_server_ready()\n");
    struct sembuf up = {0,1,0};
    semop(communication->server_ready, &up, 1);
#endif
    return;
}
