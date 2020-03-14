#include <stdio.h>
#include <stdarg.h>

#include "fmi2Functions.h"

//typedef void (*cbLogMessage) (void *instanceEnvironment, const char *instanceName, int status, const char *category, const char * message);
//
//static cbLogMessage s_cbLogMessage = NULL;

static fmi2CallbackLogger s_logger = NULL;

//void setLogger(cbLogMessage logger) {
//    s_cbLogMessage = logger;
//}

#define MAX_MESSAGE_LENGTH 2048

static void logMessage(fmi2ComponentEnvironment componentEnvironment, fmi2String instanceName, fmi2Status status, fmi2String category, fmi2String message, ...) {
    
    if (!s_logger) return;

    char buffer[MAX_MESSAGE_LENGTH];
    
    va_list args;
    va_start(args, message);
    
    vsnprintf(buffer, MAX_MESSAGE_LENGTH, message, args);

    va_end(args);
    
    s_logger(componentEnvironment, instanceName, status, category, buffer);
}

void addLoggerProxy(fmi2CallbackFunctions *functions) {
    if (functions->logger != logMessage) {
        s_logger = functions->logger;
        functions->logger = logMessage;
    }
}
