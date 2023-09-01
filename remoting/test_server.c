
#include <fmi2Functions.h>
#include <stdio.h>
#include <stdarg.h>

void logger(fmi2ComponentEnvironment componentEnvironment,
                                                fmi2String instanceName,
                                                fmi2Status status,
                                                fmi2String category,
                                                fmi2String message,
                                                ...) {

    va_list ap;

    printf("MESSAGE: ");
    va_start(ap, message);
    vprintf(message, ap);
    va_end(ap);
    printf("\n");

    return;
}


int main(int argc, char **argv) {
    fmi2CallbackFunctions function;

    function.logger = logger;
    function.allocateMemory = calloc;
    function.freeMemory = free;
    function.stepFinished = NULL;
    function.componentEnvironment = NULL;

    void *ptr = fmi2Instantiate("my_instance", fmi2CoSimulation, "fmuGUID", "fmuResourceLocation",
                    &function, fmi2True, fmi2True);

    printf("PTR = %p\n", ptr);

    return 0;
}
