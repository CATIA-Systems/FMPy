/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifndef REMOTE_H
#define REMOTE_H

#include <fmi2Functions.h>

typedef enum {
    REMOTE_fmi2GetTypesPlatform=0,
    REMOTE_fmi2GetVersion=1,
    REMOTE_fmi2SetDebugLogging=2,
    REMOTE_fmi2Instantiate=3,
    REMOTE_fmi2FreeInstance=4,
    REMOTE_fmi2SetupExperiment=5,
    REMOTE_fmi2EnterInitializationMode=6,
    REMOTE_fmi2ExitInitializationMode=7,
    REMOTE_fmi2Terminate=8,
    REMOTE_fmi2Reset=9,
    REMOTE_fmi2GetReal=10,
    REMOTE_fmi2GetInteger=11,
    REMOTE_fmi2GetBoolean=12,
    REMOTE_fmi2GetString=13,
    REMOTE_fmi2SetReal=14,
    REMOTE_fmi2SetInteger=15,
    REMOTE_fmi2SetBoolean=16,
    REMOTE_fmi2SetString=17,
    REMOTE_fmi2GetFMUstate=18,
    REMOTE_fmi2SetFMUstate=19,
    REMOTE_fmi2FreeFMUstate=20,
    REMOTE_fmi2SerializedFMUstateSize=21,
    REMOTE_fmi2SerializeFMUstate=22,
    REMOTE_fmi2DeSerializeFMUstate=23,
    REMOTE_fmi2GetDirectionalDerivative=24,

    REMOTE_fmi2EnterEventMode=25,
    REMOTE_fmi2NewDiscreteStates=26,
    REMOTE_fmi2EnterContinuousTimeMode=27,
    REMOTE_fmi2CompletedIntegratorStep=28,
    REMOTE_fmi2SetTime=29,
    REMOTE_fmi2SetContinuousStates=30,
    REMOTE_fmi2GetDerivatives=31,
    REMOTE_fmi2GetEventIndicators=32,
    REMOTE_fmi2GetContinuousStates=33,
    REMOTE_fmi2GetNominalsOfContinuousStates=34,

    REMOTE_fmi2SetRealInputDerivatives=35,
    REMOTE_fmi2GetRealOutputDerivatives=36,
    REMOTE_fmi2DoStep=37,
    REMOTE_fmi2CancelStep=38,
    REMOTE_fmi2GetStatus=39,
    REMOTE_fmi2GetRealStatus=40,
    REMOTE_fmi2GetIntegerStatus=41,
    REMOTE_fmi2GetBooleanStatus=42,
    REMOTE_fmi2GetStringStatus=43,
} remote_function_t;


/*---------------------------------------------------------------------------------
                             R E M O T E _ D A T A _ T
---------------------------------------------------------------------------------*/

#define REMOTE_MESSAGE_SIZE     8192
#define REMOTE_ARG_SIZE         65536
#define REMOTE_MAX_ARG          8
#define REMOTE_DATA_SIZE        sizeof(remote_data_t)

typedef struct {
    fmi2Status          status;
    remote_function_t   function;
    char                data[REMOTE_MAX_ARG * REMOTE_ARG_SIZE];
    char				message[REMOTE_MESSAGE_SIZE];
} remote_data_t;

typedef unsigned long portable_size_t;

/*---------------------------------------------------------------------------------
                       M A R S H A L L I N G   M A C R O S
---------------------------------------------------------------------------------*/

#define REMOTE_ARG_PTR(_data, _n)                   (_data + _n*REMOTE_ARG_SIZE)
#define REMOTE_CLEAR_ARGS(_data, _n)                memset(_data, 0, _n * REMOTE_ARG_SIZE)
#define REMOTE_ENCODE_VAR(_data, _n, _var)          memcpy(_data + _n*REMOTE_ARG_SIZE, &_var, sizeof(_var))
#define REMOTE_ENCODE_PTR(_data, _n, _ptr, _len)    memcpy(_data + _n*REMOTE_ARG_SIZE, _ptr, sizeof(*_ptr)*_len)
#define REMOTE_ENCODE_STR(_data, _n, _ptr)          strncpy(_data + _n*REMOTE_ARG_SIZE, _ptr, REMOTE_ARG_SIZE)

#define REMOTE_DECODE_VAR(_data, _n, _type)         (*((_type *)(_data + _n*REMOTE_ARG_SIZE)))    
#define REMOTE_DECODE_PTR(_data, _n, _type)         ((_type)(_data + _n*REMOTE_ARG_SIZE))
#define REMOTE_DECODE_STR(_data, _n)                REMOTE_DECODE_PTR(_data, _n, fmi2String)


/*-----------------------------------------------------------------------------
                               P R O T O T Y P E S
-----------------------------------------------------------------------------*/

extern void remote_clear_args(int n);
extern void remote_encode_strings(const char *const src[], char* dst, size_t ns);
extern void remote_decode_strings(const char* src, const char* dst[], size_t ns);
extern const char* remote_function_name(remote_function_t function);

#endif
