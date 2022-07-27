#ifndef config_h
#define config_h

// define class name and unique id
#define MODEL_IDENTIFIER VanDerPol
#define INSTANTIATION_TOKEN "{8c4e810f-3da3-4a00-8276-176fa3c9f000}"

#define CO_SIMULATION
#define MODEL_EXCHANGE

// define model size
#define NX 2
#define NZ 0

#define SET_FLOAT64

#define GET_PARTIAL_DERIVATIVE

#define FIXED_SOLVER_STEP 1e-2
#define DEFAULT_STOP_TIME 20

typedef enum {
    vr_time, vr_x0, vr_der_x0, vr_x1, vr_der_x1, vr_mu
} ValueReference;

typedef struct {

    double x0;
    double der_x0;
    double x1;
    double der_x1;
    double mu;

} ModelData;

#endif /* config_h */
