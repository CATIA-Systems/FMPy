#include <stdio.h>
#include <stdarg.h>
#include "fmi2Functions.h"

#define MAX_MESSAGE_LENGTH 2048


static fmi2CallbackLogger s_logger = NULL;


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
