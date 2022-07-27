#include "config.h"
#include "model.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include "shlwapi.h"
#pragma comment(lib, "shlwapi.lib")
#endif

#define MAX_PATH_LENGTH 4096

void setStartValues(ModelInstance *comp) {
    M(y) = 0;
}

Status calculateValues(ModelInstance *comp) {

    // load the file
    FILE *file = NULL;
    char path[MAX_PATH_LENGTH] = "";
    char c = '\0';

    if (!comp->resourceLocation) {
        logError(comp, "Resource location must not be NULL.");
        return Error;
    }

#ifdef _WIN32

#if FMI_VERSION < 3
    DWORD pathLen = MAX_PATH_LENGTH;

    if (PathCreateFromUrlA(comp->resourceLocation, path, &pathLen, 0) != S_OK) {
        logError(comp, "Failed to convert resource location to file system path.");
        return Error;
    }
#else
    strncpy(path, comp->resourceLocation, MAX_PATH_LENGTH);
#endif

#if FMI_VERSION == 1
    if (!PathAppendA(path, "resources") || !PathAppendA(path, "y.txt")) return Error;
#elif FMI_VERSION == 2
    if (!PathAppendA(path, "y.txt")) return Error;
#else
    if (!strncat(path, "y.txt", MAX_PATH_LENGTH)) return Error;
#endif

#else

#if FMI_VERSION < 3
    const char *scheme1 = "file:///";
    const char *scheme2 = "file:/";

    if (strncmp(comp->resourceLocation, scheme1, strlen(scheme1)) == 0) {
        strncpy(path, &comp->resourceLocation[strlen(scheme1)] - 1, MAX_PATH_LENGTH-1);
    } else if (strncmp(comp->resourceLocation, scheme2, strlen(scheme2)) == 0) {
        strncpy(path, &comp->resourceLocation[strlen(scheme2) - 1], MAX_PATH_LENGTH-1);
    } else {
        logError(comp, "The resourceLocation must start with \"file:/\" or \"file:///\"");
        return Error;
    }
#else
    strncpy(path, comp->resourceLocation, MAX_PATH_LENGTH);
#endif

#if FMI_VERSION == 1
    strncat(path, "/resources/y.txt", MAX_PATH_LENGTH-strlen(path)-1);
#elif FMI_VERSION == 2
    strncat(path, "/y.txt", MAX_PATH_LENGTH-strlen(path)-1);
#else
    strncat(path, "y.txt", MAX_PATH_LENGTH-strlen(path)-1);
#endif
    path[MAX_PATH_LENGTH-1] = 0;

#endif

    // open the resource file
    file = fopen (path, "r");

    if (!file) {
        logError(comp, "Failed to open resource file %s.", path);
        return Error;
    }

    // read the first character
    c = (char)fgetc(file);

    // assign it to y
    M(y) = c;

    // close the file
    fclose(file);

    return OK;
}


Status getFloat64(ModelInstance* comp, ValueReference vr, double *value, size_t *index) {
    switch (vr) {
    case vr_time:
        value[(*index)++] = comp->time;
        return OK;
    default:
        logError(comp, "Get Float64 is not allowed for value reference %u.", vr);
        return Error;
    }
}


Status getInt32(ModelInstance* comp, ValueReference vr, int *value, size_t *index) {
    switch (vr) {
        case vr_y:
            value[(*index)++] = M(y);
            return OK;
        default:
            logError(comp, "Get Int32 is not allowed for value reference %u.", vr);
            return Error;
    }
}

void eventUpdate(ModelInstance *comp) {
    comp->valuesOfContinuousStatesChanged   = false;
    comp->nominalsOfContinuousStatesChanged = false;
    comp->terminateSimulation               = false;
    comp->nextEventTimeDefined              = false;
}
