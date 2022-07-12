#include "ModelicaUtilities.h"
#include "ModelicaUtilityFunctions.h"

#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>

static ModelicaUtilityFunctions_t s_callbacks = { NULL };


void setModelicaUtilityFunctions(ModelicaUtilityFunctions_t *callbacks) {
	s_callbacks = *callbacks;
}


void ModelicaMessage(const char *string) {

	if (s_callbacks.ModelicaMessage) {
		s_callbacks.ModelicaMessage(string);
	} else {
		printf(string);
	}
}


void ModelicaFormatMessage(const char *string, ...) {

	va_list vl;
	va_start(vl, string);

	if (s_callbacks.ModelicaVFormatMessage) {
		s_callbacks.ModelicaVFormatMessage(string, vl);
	} else {
		vprintf(string, vl);
	}

	va_end(vl);
}


void ModelicaVFormatMessage(const char *string, va_list vl) {

	if (s_callbacks.ModelicaVFormatMessage) {
		s_callbacks.ModelicaVFormatMessage(string, vl);
	} else {
		vprintf(string, vl);
	}
}


void ModelicaError(const char *string) {

	if (s_callbacks.ModelicaError) {
		s_callbacks.ModelicaError(string);
	} else {
		printf(string);
	}
}


void ModelicaFormatError(const char *string, ...) {

	va_list vl;
	va_start(vl, string);

	if (s_callbacks.ModelicaVFormatError) {
		s_callbacks.ModelicaVFormatError(string, vl);
	} else {
		vprintf(string, vl);
		exit(1);
	}

	va_end(vl);
}


void ModelicaVFormatError(const char *string, va_list vl) {

	if (s_callbacks.ModelicaVFormatError) {
		s_callbacks.ModelicaVFormatError(string, vl);
	} else {
		vprintf(string, vl);
		exit(1);
	}
}


char* ModelicaAllocateString(size_t len) {
	return (char*)malloc(len); 
}


char* ModelicaAllocateStringWithErrorReturn(size_t len) { 
	return (char*)malloc(len);
}
