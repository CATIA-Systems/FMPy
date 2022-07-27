#ifndef cosimulation_h
#define cosimulation_h

#include "model.h"

#define EPSILON (FIXED_SOLVER_STEP * 1e-6)

void doFixedStep(ModelInstance *comp, bool* stateEvent, bool* timeEvent);

#endif /* cosimulation_h */
