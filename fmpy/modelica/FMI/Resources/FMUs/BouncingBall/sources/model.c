#include <math.h>  // for fabs()
#include <float.h> // for DBL_MIN
#include "config.h"
#include "model.h"

#define V_MIN (0.1)

void setStartValues(ModelInstance *comp) {
    M(h) =  1;
    M(v) =  0;
    M(g) = -9.81;
    M(e) =  0.7;
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
        case vr_h:
            value[(*index)++] = M(h);
            return OK;
        case vr_der_h:
        case vr_v:
            value[(*index)++] = M(v);
            return OK;
        case vr_der_v:
        case vr_g:
            value[(*index)++] = M(g);
            return OK;
        case vr_e:
            value[(*index)++] = M(e);
            return OK;
        case vr_v_min:
            value[(*index)++] = V_MIN;
            return OK;
        default:
            logError(comp, "Get Float64 is not allowed for value reference %u.", vr);
            return Error;
    }
}

Status setFloat64(ModelInstance* comp, ValueReference vr, const double *value, size_t *index) {
    switch (vr) {

        case vr_h:
            M(h) = value[(*index)++];
            return OK;

        case vr_v:
            M(v) = value[(*index)++];
            return OK;

        case vr_g:
#if FMI_VERSION > 1
            if (comp->type == ModelExchange &&
                comp->state != Instantiated &&
                comp->state != InitializationMode) {
                logError(comp, "Variable g can only be set after instantiation or in initialization mode.");
                return Error;
            }
#endif
            M(g) = value[(*index)++];
            return OK;

        case vr_e:
#if FMI_VERSION > 1
            if (comp->type == ModelExchange &&
                comp->state != Instantiated &&
                comp->state != InitializationMode &&
                comp->state != EventMode) {
                logError(comp, "Variable e can only be set after instantiation, in initialization mode or event mode.");
                return Error;
            }
#endif
            M(e) = value[(*index)++];
            return OK;

        case vr_v_min:
            logError(comp, "Variable v_min (value reference %u) is constant and cannot be set.", vr_v_min);
            return Error;

        default:
            logError(comp, "Unexpected value reference: %u.", vr);
            return Error;
    }
}

Status getOutputDerivative(ModelInstance *comp, ValueReference valueReference, int order, double *value) {

    if (order != 1) {
        logError(comp, "The output derivative order %d for value reference %u is not available.", order, valueReference);
        return Error;
    }

    switch (valueReference) {
    case vr_h:
        *value = M(v);
        return OK;
    case vr_v:
        *value = M(g);
        return OK;
    default:
        logError(comp, "The output derivative for value reference %u is not available.", valueReference);
        return Error;
    }
}

void eventUpdate(ModelInstance *comp) {

    if (M(h) <= 0 && M(v) < 0) {

        M(h) = DBL_MIN;  // slightly above 0 to avoid zero-crossing
        M(v) = -M(v) * M(e);

        if (M(v) < V_MIN) {
            // stop bouncing
            M(v) = 0;
            M(g) = 0;
        }

        // reset previous event indicators
        getEventIndicators(comp, comp->z, NZ);

        comp->valuesOfContinuousStatesChanged = true;
    }

    comp->nominalsOfContinuousStatesChanged = false;
    comp->terminateSimulation  = false;
    comp->nextEventTimeDefined = false;
}

void getContinuousStates(ModelInstance *comp, double x[], size_t nx) {
    UNUSED(nx);
    x[0] = M(h);
    x[1] = M(v);
}

void setContinuousStates(ModelInstance *comp, const double x[], size_t nx) {
    UNUSED(nx);
    M(h) = x[0];
    M(v) = x[1];
}

void getDerivatives(ModelInstance *comp, double dx[], size_t nx) {
    UNUSED(nx);
    dx[0] = M(v);
    dx[1] = M(g);
}

void getEventIndicators(ModelInstance *comp, double z[], size_t nz) {
    UNUSED(nz);
    z[0] = (M(h) == 0 && M(v) == 0) ? 1 : M(h);
}
