#include <float.h>  // for DBL_EPSILON
#include <math.h>   // for fabs()
#include "config.h"
#include "model.h"


void setStartValues(ModelInstance *comp) {
    M(counter) = 1;

    // TODO: move this to initialize()?
    comp->nextEventTime        = 1;
    comp->nextEventTimeDefined = true;
}

Status calculateValues(ModelInstance *comp) {
    UNUSED(comp);
    // nothing to do
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
        case vr_counter:
            value[(*index)++] = M(counter);
            return OK;
        default:
            logError(comp, "Get Int32 is not allowed for value reference %u.", vr);
            return Error;
    }
}

void eventUpdate(ModelInstance *comp) {

    double epsilon = (1.0 + fabs(comp->time)) * DBL_EPSILON;

    if (comp->nextEventTimeDefined && comp->time + epsilon >= comp->nextEventTime) {
        M(counter)++;
        comp->nextEventTime += 1;
    }

    comp->valuesOfContinuousStatesChanged   = false;
    comp->nominalsOfContinuousStatesChanged = false;
    comp->terminateSimulation               = M(counter) >= 10;
    comp->nextEventTimeDefined              = true;
}
