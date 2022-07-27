#ifndef config_h
#define config_h

#include <stddef.h>  // for size_t
#include <stdbool.h> // for bool
#include <inttypes.h>

// define class name and unique id
#define MODEL_IDENTIFIER Feedthrough
#define INSTANTIATION_TOKEN "{8c4e810f-3df3-4a00-8276-176fa3c9f004}"

#define CO_SIMULATION
#define MODEL_EXCHANGE

#define NX 0
#define NZ 0

#define GET_FLOAT32
#define GET_FLOAT64
#define GET_INT8
#define GET_UINT8
#define GET_INT16
#define GET_UINT16
#define GET_INT32
#define GET_UINT32
#define GET_INT64
#define GET_UINT64
#define GET_BOOLEAN
#define GET_STRING
#define GET_BINARY

#define SET_FLOAT32
#define SET_FLOAT64
#define SET_INT8
#define SET_UINT8
#define SET_INT16
#define SET_UINT16
#define SET_INT32
#define SET_UINT32
#define SET_INT64
#define SET_UINT64
#define SET_BOOLEAN
#define SET_STRING
#define SET_BINARY

#define EVENT_UPDATE

#define FIXED_SOLVER_STEP 0.1
#define DEFAULT_STOP_TIME 2

#define STRING_MAX_LEN 128
#define BINARY_MAX_LEN 128

typedef enum {

    vr_time,

    vr_Float32_continuous_input,
    vr_Float32_continuous_output,
    vr_Float32_discrete_input,
    vr_Float32_discrete_output,

    vr_Float64_fixed_parameter,
    vr_Float64_tunable_parameter,
    vr_Float64_continuous_input,
    vr_Float64_continuous_output,
    vr_Float64_discrete_input,
    vr_Float64_discrete_output,

    vr_Int8_input,
    vr_Int8_output,

    vr_UInt8_input,
    vr_UInt8_output,

    vr_Int16_input,
    vr_Int16_output,

    vr_UInt16_input,
    vr_UInt16_output,

    vr_Int32_input,
    vr_Int32_output,

    vr_UInt32_input,
    vr_UInt32_output,

    vr_Int64_input,
    vr_Int64_output,

    vr_UInt64_input,
    vr_UInt64_output,

    vr_Boolean_input,
    vr_Boolean_output,

    vr_String_parameter,

    vr_Binary_input,
    vr_Binary_output,

} ValueReference;

typedef struct {

    float Float32_continuous_input;
    float Float32_continuous_output;
    float Float32_discrete_input;
    float Float32_discrete_output;

    double Float64_fixed_parameter;
    double Float64_tunable_parameter;
    double Float64_continuous_input;
    double Float64_continuous_output;
    double Float64_discrete_input;
    double Float64_discrete_output;

    int8_t Int8_input;
    int8_t Int8_output;

    uint8_t UInt8_input;
    uint8_t UInt8_output;

    int16_t Int16_input;
    int16_t Int16_output;

    uint16_t UInt16_input;
    uint16_t UInt16_output;

    int32_t Int32_input;
    int32_t Int32_output;

    uint32_t UInt32_input;
    uint32_t UInt32_output;

    int64_t Int64_input;
    int64_t Int64_output;

    uint64_t UInt64_input;
    uint64_t UInt64_output;

    bool Boolean_input;
    bool Boolean_output;

    char String_parameter[STRING_MAX_LEN];

    size_t Binary_input_size;
    char Binary_input[BINARY_MAX_LEN];
    size_t Binary_output_size;
    char Binary_output[BINARY_MAX_LEN];

} ModelData;

extern const char* STRING_START;
extern const char* BINARY_START;

#endif /* config_h */
