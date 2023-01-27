#ifdef _WIN32
#include <Windows.h>
#else
#include <pthread.h>
#endif

#include "FMI.h"


typedef struct {

    size_t size;
    size_t* ci;
    FMIValueReference* vr;

} VariableMapping;

typedef struct {

    FMIVariableType type;
    size_t startComponent;
    FMIValueReference startValueReference;
    size_t endComponent;
    FMIValueReference endValueReference;

} Connection;

typedef struct {

    FMIInstance* instance;

#ifdef _WIN32
    HANDLE thread;
    HANDLE mutex;
#else
    pthread_t thread;
    pthread_mutex_t mutex;
#endif

    double currentCommunicationPoint;
    double communicationStepSize;
    FMIStatus status;
    bool doStep;
    bool terminate;

} Component;

typedef struct {

    FMIVersion fmiVersion;

    const char* instanceName;

    void* instanceEnvironment;
    
    void* logMessage;

    size_t nComponents;
    Component** components;

    size_t nVariables;
    VariableMapping* variables;

    size_t nConnections;
    Connection* connections;

    bool parallelDoStep;

    double time;

} System;


System* instantiateSystem(
    FMIVersion fmiVersion,
    const char* resourcesDir,
    const char* instanceName,
    void* logMessage,
    void* instanceEnvironment, 
    bool loggingOn, 
    bool visible);

FMIStatus doStep(
    System* s,
    double  currentCommunicationPoint,
    double  communicationStepSize,
    bool    noSetFMUStatePriorToCurrentPoint);


FMIStatus terminateSystem(System* s);

FMIStatus resetSystem(System* s);

void freeSystem(System* s);
