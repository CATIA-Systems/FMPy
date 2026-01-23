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
    DECLARE_FMI_CALLBACK(fmi2SetReal);
    DECLARE_FMI_CALLBACK(fmi2SetInteger);
    DECLARE_FMI_CALLBACK(fmi2SetBoolean);
    DECLARE_FMI_CALLBACK(fmi2DoStep);
} fmu_entries_t;
#undef DECLARE_FMI_CALLBACK


/*-----------------------------------------------------------------------------
                                S E R V E R _ T
-----------------------------------------------------------------------------*/
typedef struct {
    fmi2Real                *value;
    fmi2ValueReference      *vr;
} server_data_reals_t;

typedef struct {
    fmi2Integer             *value;
    fmi2ValueReference      *vr;
} server_data_integers_t;

typedef struct {
    fmi2Boolean             *value;
    fmi2ValueReference      *vr;
} server_data_booleans_t;

typedef struct {
    server_data_reals_t            reals;
    server_data_integers_t         integers;
    server_data_booleans_t         booleans;
} server_data_t;


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
    communication_data_t	data;
    server_data_t           update;
} server_t;


#endif
