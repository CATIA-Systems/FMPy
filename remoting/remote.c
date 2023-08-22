/*    ___                                               __   __
 *  .'  _|.--------.--.--.  .----.-----.--------.-----.|  |_|__|.-----.-----.
 *  |   _||        |  |  |  |   _|  -__|        |  _  ||   _|  ||     |  _  |
 *  |__|  |__|__|__|_____|  |__| |_____|__|__|__|_____||____|__||__|__|___  |
 *  Copyright 2023 Renault SAS                                        |_____|
 *  The remoting code is written by Nicolas.LAURENT@Renault.com.
 *  This code is released under the 2-Clause BSD license.
 */

#include <string.h>
#if WIN32
#   pragma warning(disable: 4996) /* Stop complaining about strdup() */
#endif

#include "remote.h"

void remote_encode_strings(const char* const src[], char* dst, size_t ns) {
	char* off = dst;
	size_t remaining = REMOTE_ARG_SIZE;
	for(size_t i = 0; i < ns; i += 1) {
		size_t len = strlen(src[i]) + 1;
		strncat(off, src[i], remaining);
		off += len;
		remaining -= len;
		if (remaining <= 0)
			break;
	}
}


void remote_decode_strings(const char* src, const char* dst[], size_t ns) {
	const char* off = src;
	size_t remaining = REMOTE_ARG_SIZE;
	for (size_t i = 0; i < ns; i += 1) {
		size_t len = strlen(off) + 1;
		dst[i] = strdup(off);
		off += len;
		remaining -= len;
		if (remaining <= 0)
			break;
	}
}


const char *remote_function_name(remote_function_t function) {

#define CASE(x) case REMOTE_ ## x: return #x
    switch (function) {
        CASE(fmi2GetTypesPlatform);
        CASE(fmi2GetVersion);
        CASE(fmi2SetDebugLogging);
        CASE(fmi2Instantiate);
        CASE(fmi2FreeInstance);
        CASE(fmi2SetupExperiment);
        CASE(fmi2EnterInitializationMode);
        CASE(fmi2ExitInitializationMode);
        CASE(fmi2Terminate);
        CASE(fmi2Reset);
        CASE(fmi2GetReal);
        CASE(fmi2GetInteger);
        CASE(fmi2GetBoolean);
        CASE(fmi2GetString);
        CASE(fmi2SetReal);
        CASE(fmi2SetInteger);
        CASE(fmi2SetBoolean);
        CASE(fmi2SetString);
        CASE(fmi2GetFMUstate);
        CASE(fmi2SetFMUstate);
        CASE(fmi2FreeFMUstate);
        CASE(fmi2SerializedFMUstateSize);
        CASE(fmi2SerializeFMUstate);
        CASE(fmi2DeSerializeFMUstate);
        CASE(fmi2GetDirectionalDerivative);

        CASE(fmi2EnterEventMode);
        CASE(fmi2NewDiscreteStates);
        CASE(fmi2EnterContinuousTimeMode);
        CASE(fmi2CompletedIntegratorStep);
        CASE(fmi2SetTime);
        CASE(fmi2SetContinuousStates);
        CASE(fmi2GetDerivatives);
        CASE(fmi2GetEventIndicators);
        CASE(fmi2GetContinuousStates);
        CASE(fmi2GetNominalsOfContinuousStates);

        CASE(fmi2SetRealInputDerivatives);
        CASE(fmi2GetRealOutputDerivatives);
        CASE(fmi2DoStep);
        CASE(fmi2CancelStep);
        CASE(fmi2GetStatus);
        CASE(fmi2GetRealStatus);
        CASE(fmi2GetIntegerStatus);
        CASE(fmi2GetBooleanStatus);
        CASE(fmi2GetStringStatus);
	}
	return "UNKNOWN";
}
