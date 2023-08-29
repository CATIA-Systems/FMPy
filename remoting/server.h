/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#ifndef SERVER_H
#define SERVER_H

#include <fmi2Functions.h>

#include "communication.h"
#include "process.h"
#include "remote.h"

/*----------------------------------------------------------------------------
                            F M U _ L I B R A R Y T
----------------------------------------------------------------------------*/

#ifdef WIN32
typedef HINSTANCE library_t;
#else
typedef void* library_t;
#endif


/*----------------------------------------------------------------------------
                           F M U _ E N T R I E S _ T
----------------------------------------------------------------------------*/
/*
 * List all interesting entry points of a shared object (DLL)
 * It may contain multiple versions of FMI API.
 */
#define DECLARE_FMI_CALLBACK(x) x ## TYPE *x
typedef struct {
    /* FMI2 functions */
    DECLARE_FMI_CALLBACK(fmi2GetTypesPlatform);
    DECLARE_FMI_CALLBACK(fmi2GetVersion);
    DECLARE_FMI_CALLBACK(fmi2SetDebugLogging);
    DECLARE_FMI_CALLBACK(fmi2Instantiate);
    DECLARE_FMI_CALLBACK(fmi2FreeInstance);
    DECLARE_FMI_CALLBACK(fmi2SetupExperiment);
    DECLARE_FMI_CALLBACK(fmi2EnterInitializationMode);
    DECLARE_FMI_CALLBACK(fmi2ExitInitializationMode);
    DECLARE_FMI_CALLBACK(fmi2Terminate);
    DECLARE_FMI_CALLBACK(fmi2Reset);
    DECLARE_FMI_CALLBACK(fmi2GetReal);
    DECLARE_FMI_CALLBACK(fmi2GetInteger);
    DECLARE_FMI_CALLBACK(fmi2GetBoolean);
    DECLARE_FMI_CALLBACK(fmi2GetString);
    DECLARE_FMI_CALLBACK(fmi2SetReal);
    DECLARE_FMI_CALLBACK(fmi2SetInteger);
    DECLARE_FMI_CALLBACK(fmi2SetBoolean);
    DECLARE_FMI_CALLBACK(fmi2SetString);
    DECLARE_FMI_CALLBACK(fmi2GetFMUstate);
    DECLARE_FMI_CALLBACK(fmi2SetFMUstate);
    DECLARE_FMI_CALLBACK(fmi2FreeFMUstate);
    DECLARE_FMI_CALLBACK(fmi2SerializedFMUstateSize);
    DECLARE_FMI_CALLBACK(fmi2SerializeFMUstate);
    DECLARE_FMI_CALLBACK(fmi2DeSerializeFMUstate);
    DECLARE_FMI_CALLBACK(fmi2GetDirectionalDerivative);
    DECLARE_FMI_CALLBACK(fmi2SetRealInputDerivatives);
    DECLARE_FMI_CALLBACK(fmi2GetRealOutputDerivatives);
    DECLARE_FMI_CALLBACK(fmi2DoStep);
    DECLARE_FMI_CALLBACK(fmi2CancelStep);
    DECLARE_FMI_CALLBACK(fmi2GetStatus);
    DECLARE_FMI_CALLBACK(fmi2GetRealStatus);
    DECLARE_FMI_CALLBACK(fmi2GetIntegerStatus);
    DECLARE_FMI_CALLBACK(fmi2GetBooleanStatus);
    DECLARE_FMI_CALLBACK(fmi2GetStringStatus);

    DECLARE_FMI_CALLBACK(fmi2EnterEventMode);
    DECLARE_FMI_CALLBACK(fmi2NewDiscreteStates);
    DECLARE_FMI_CALLBACK(fmi2EnterContinuousTimeMode);
    DECLARE_FMI_CALLBACK(fmi2GetNominalsOfContinuousStates);
    DECLARE_FMI_CALLBACK(fmi2GetDerivatives);
    DECLARE_FMI_CALLBACK(fmi2GetContinuousStates);
    DECLARE_FMI_CALLBACK(fmi2CompletedIntegratorStep);
    DECLARE_FMI_CALLBACK(fmi2SetTime);
    DECLARE_FMI_CALLBACK(fmi2SetContinuousStates);
    DECLARE_FMI_CALLBACK(fmi2GetEventIndicators);
} fmu_entries_t;
#undef DECLARE_FMI_CALLBACK


/*-----------------------------------------------------------------------------
                                S E R V E R _ T
-----------------------------------------------------------------------------*/

typedef struct {
	communication_t         *communication;
    fmu_entries_t           entries;
    library_t               library;
    const char              *library_filename;
    fmi2Component           component;
    char                    *instance_name;
    fmi2CallbackFunctions   functions;
    int                     is_debug;
    process_handle_t        parent_handle;
    char				    shared_key[COMMUNICATION_KEY_LEN];
} server_t;


#endif
