#ifndef config_h
#define config_h

// define class name and unique id
#define MODEL_IDENTIFIER BouncingBall
#define INSTANTIATION_TOKEN "{8c4e810f-3df3-4a00-8276-176fa3c9f003}"

#define CO_SIMULATION
#define MODEL_EXCHANGE

// define model size
#define NX 2
#define NZ 1

#define SET_FLOAT64
#define GET_OUTPUT_DERIVATIVE
#define EVENT_UPDATE

#define FIXED_SOLVER_STEP 1e-3
#define DEFAULT_STOP_TIME 3

typedef enum {
    vr_time, vr_h, vr_der_h, vr_v, vr_der_v, vr_g, vr_e, vr_v_min
} ValueReference;

typedef struct {

    double h;
    double v;
    double g;
    double e;

} ModelData;

#endif /* config_h */
