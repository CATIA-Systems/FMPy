#include "config.h"

#include <stdlib.h>
#include <string.h>
#ifndef WIN32
#   define _GNU_SOURCE  /* to access to semtimedop() if available */
#   include <errno.h>
#   include <stdio.h>
#   include <unistd.h>
#   ifndef HAVE_SEMTIMEDOP
#       include <signal.h>
#   endif
#   include <sys/ipc.h>
#   include <sys/sem.h>
#   include <sys/time.h>
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


#if !defined WIN32 && !defined HAVE_SEMTIMEDOP
static void communication_alarm_handler(int sig) {
    /* this nop signal handler is needed to make semop() interruptible */
    return;
}
#endif


static sem_handle_t communication_sem_create(const char *name) {
    sem_handle_t sem;

#ifdef WIN32
    sem = CreateSemaphoreA(NULL, 0, 1, name);
#else
    SHM_LOG("Create SEM %s\n", name);
    FILE *sem_file = fopen(name, "w");
    if (!sem_file) 
        return SEM_INVALID;
    fclose(sem_file);
    sem = semget(ftok(name, 0), 1, IPC_CREAT | IPC_EXCL | 0600);
#endif

    return sem;
}


static sem_handle_t communication_sem_join(const char *name) {
    sem_handle_t sem;

#ifdef WIN32
    sem = CreateSemaphoreA(NULL, 0, 1, name);
#else
    SHM_LOG("Join SEM %s\n", name);
    sem = semget(ftok(name, 0), 1, 0600);
#endif

    return sem;
}


static void communication_sem_free(sem_handle_t sem, const char *sem_name) {
    if (sem)
#ifdef WIN32
       CloseHandle(sem);
#else
        SHM_LOG("communication_sem_free(%s)\n", sem_name);
        semctl(sem, 0, IPC_RMID); /* silently ignore error if any */
        unlink(sem_name);  /* silently ignore error if any */
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
        (DWORD)memory_size,             // maximum object size (low-order DWORD)
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

    communication_shm_unmap(communication->shm, communication->data_size);
    communication_shm_free(communication->map_file, communication->shm_name);

    communication_sem_free(communication->server_ready, communication->sem_name_server);
    communication_sem_free(communication->client_ready, communication->sem_name_client);

    free(communication->sem_name_client);
    free(communication->sem_name_server);
    free(communication->shm_name);

    free(communication);
}

static size_t communication_shm_size(unsigned long nb_reals, unsigned long nb_integers, unsigned long nb_booleans) {
    size_t size = sizeof(communication_shm_t);
    size +=  nb_reals * (sizeof(fmi2Real) + sizeof(fmi2ValueReference) + sizeof(bool));
    size +=  nb_integers * (sizeof(fmi2Integer) + sizeof(fmi2ValueReference) + sizeof(bool));
    size +=  nb_booleans * (sizeof(fmi2Boolean) + sizeof(fmi2ValueReference) + sizeof(bool));
    return size;
} 

void communication_data_initialize(communication_data_t *data, communication_t *communication) {
    char *ptr = (char *)communication->shm + sizeof(communication_shm_t);

    /* REALS */
    data->reals.value = (void *)ptr;
    ptr += sizeof(*data->reals.value) * communication->nb_reals;

    data->reals.vr = (void*)ptr;
    ptr += sizeof(*data->reals.vr) * communication->nb_reals;

    data->reals.changed = (void*)ptr;
    ptr += sizeof(*data->reals.changed) * communication->nb_reals;
    
    /* INTEGERS */
    data->integers.value = (void *)ptr;
    ptr += sizeof(*data->integers.value) * communication->nb_integers;

    data->integers.vr = (void*)ptr;
    ptr += sizeof(*data->integers.vr) * communication->nb_integers;

    data->integers.changed = (void*)ptr;
    ptr += sizeof(*data->integers.changed) * communication->nb_integers;


    /* BOOLEANS */
    data->booleans.value = (void *)ptr;
    ptr += sizeof(*data->booleans.value) * communication->nb_booleans;

    data->booleans.vr = (void *)ptr;
    ptr += sizeof(*data->booleans.vr) * communication->nb_booleans;

    data->booleans.changed = (void *)ptr;
    ptr += sizeof(*data->booleans.changed) * communication->nb_booleans; /* not needed */

    return;
}

static int communication_new_client(communication_t *communication) {
    communication->client_ready = communication_sem_create(communication->sem_name_client);
    if (communication->client_ready == SEM_INVALID) {
        SHM_LOG("Client: Cannot Create Semaphore(%s): %s\n", communication->sem_name_client, strerror(errno));
        return -1;
    }

    communication->server_ready = communication_sem_create(communication->sem_name_server);
    if (communication->server_ready == SEM_INVALID) {
        SHM_LOG("Client: Cannot Create Semaphore(%s): %s\n", communication->sem_name_server, strerror(errno));
        return -1;
    }

    /* 1st. CLIENT should create memory and notify the client */
    SHM_LOG("Client: Create SHM...\n");
    communication->map_file = communication_shm_create(communication->shm_name, communication->data_size);
    SHM_LOG("Client: communication->map_file = %p\n", communication->map_file);
    if (communication->map_file == SHM_INVALID) {
        SHM_LOG("ERROR: Cannot open or create map file.\n");
        return -1;
    }
    SHM_LOG("Client: Map SHM...\n");
    communication->shm = communication_shm_map(communication->map_file, communication->data_size);
    SHM_LOG("Client: communication->shm = %p\n", communication->shm);
    if (!communication->shm) {
        SHM_LOG("ERROR: Cannot map SHM.\n");
        return -1;
    }

    communication_client_ready(communication);


    return 0;
}


static int communication_new_server(communication_t *communication) {
    communication->client_ready = communication_sem_join(communication->sem_name_client);
    if (communication->client_ready == SEM_INVALID) {
        SHM_LOG("Server: Cannot Join Semaphore(%s): %s\n", communication->sem_name_client, strerror(errno));
        return -1;
    }

    communication->server_ready = communication_sem_join(communication->sem_name_server);
    if (communication->server_ready == SEM_INVALID) {
        SHM_LOG("Server: Cannot Join Semaphore(%s): %s\n", communication->sem_name_server, strerror(errno));
        return -1;
    }

    /* 2nd. Server should wait for memory creation by client and connect to it */
    SHM_LOG("Wait for client to initialize SHM.\n");
    communication_waitfor_client(communication);
    SHM_LOG("Client ready. Joining SHM\n");
    communication->map_file = communication_shm_join(communication->shm_name);
    communication->shm = communication_shm_map(communication->map_file, communication->data_size);
    if (!communication->shm) {
        SHM_LOG("ERROR: Cannot map SHM.\n");
        return -1;
    }

    return 0;
}


communication_t *communication_new(const char *prefix, unsigned long nb_reals,
	unsigned long nb_integers, unsigned long nb_booleans, communication_endpoint_t endpoint) {
    communication_t* communication = malloc(sizeof(*communication));
    if (!communication)
        return NULL;

    communication->endpoint = endpoint;
    communication->nb_reals = nb_reals;
    communication->nb_integers = nb_integers;
    communication->nb_booleans = nb_booleans;
#ifdef WIN32
    communication->sem_name_client = concat(prefix, "_client");
    communication->sem_name_server = concat(prefix, "_server");
#else
    /* on Unix, semaphores require an existing file
       it will be created in sem_create() functions */
    char *tmp_prefix = concat("/tmp", prefix);
    communication->sem_name_client = concat(tmp_prefix, "_client");
    communication->sem_name_server = concat(tmp_prefix, "_server");
    free(tmp_prefix);
#endif

    communication->shm_name = concat(prefix, "_memory");
    communication->shm = NULL;
    communication->map_file = SHM_INVALID;
    communication->data_size = communication_shm_size(nb_reals, nb_integers, nb_booleans);

    SHM_LOG("Initialize SHM size=%ld (nb_reals=%lu, nb_integers=%lu, nb_booleans=%lu)\n",
        communication->data_size,
        nb_reals, nb_integers, nb_booleans);
    int status;
    if (endpoint == COMMUNICATION_CLIENT) {
        status = communication_new_client(communication);
    } else {
        status = communication_new_server(communication);
    }
    
    if (status) {
        communication_free(communication);
        return NULL;
    }

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
    struct timespec ts_timeout;
    ts_timeout.tv_sec = timeout / 1000;
    ts_timeout.tv_nsec = (timeout - ts_timeout.tv_sec * 1000) * 1000000;
    int status = semtimedop(communication->server_ready, &down, 1, &ts_timeout);
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
    struct timespec ts_timeout;
    ts_timeout.tv_sec = timeout / 1000;
    ts_timeout.tv_nsec = (timeout - ts_timeout.tv_sec * 1000) * 1000000;
    int status = semtimedop(communication->client_ready, &down, 1, &ts_timeout);
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
