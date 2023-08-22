
#include <dlfcn.h>
#include <fmi2Functions.h>
#include <stdio.h>
#include <stdarg.h>

void logger(fmi2ComponentEnvironment componentEnvironment,
fmi2String instanceName, fmi2Status status, fmi2String category,
fmi2String message, ...) {

    va_list ap;

    printf("instance=%s status=%d category=%s | ", instanceName, status, category);
    va_start(ap, message);
    vprintf(message, ap);
    va_end(ap);
    printf("\n");

    return;
}


int main(int argc, char **argv) {

    void *lib=dlopen(argv[1], RTLD_LAZY);
    if (! lib) {
        printf("Cannot open %s: %s\n", argv[1], dlerror());
        return -1;
    }

    fmi2InstantiateTYPE *instantiate = dlsym(lib, "fmi2Instantiate");
    if (! instantiate) {
        printf("Cannot find fmi2Instantiate\n");
        return -2;
    }

    fmi2CallbackFunctions function;

    function.logger = logger;
    function.allocateMemory = calloc;
    function.freeMemory = free;
    function.stepFinished = NULL;
    function.componentEnvironment = NULL;

    void *ptr = instantiate("my_instance", fmi2CoSimulation, "{8c4e810f-3da3-4a00-8276-176fa3c9f000}", "fmuResourceLocation",
                    &function, fmi2True, fmi2True);

    printf("PTR = %p\n", ptr);

    return 0;
}
