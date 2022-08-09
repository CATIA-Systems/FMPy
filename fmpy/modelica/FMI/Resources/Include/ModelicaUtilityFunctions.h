#ifndef MODELICA_UTILITY_FUNCTIONS_H
#define MODELICA_UTILITY_FUNCTIONS_H

#include <stdarg.h>
#include <stddef.h>


typedef struct {

	void  (*ModelicaMessage)(const char *string);
	void  (*ModelicaFormatMessage)(const char *string, ...);
	void  (*ModelicaVFormatMessage)(const char *string, va_list);
	void  (*ModelicaError)(const char *string);
	void  (*ModelicaFormatError)(const char *string, ...);
	void  (*ModelicaVFormatError)(const char *string, va_list);
	char* (*ModelicaAllocateString)(size_t len);
	char* (*ModelicaAllocateStringWithErrorReturn)(size_t len);

} ModelicaUtilityFunctions_t;

void setModelicaUtilityFunctions(ModelicaUtilityFunctions_t *callbacks);

#endif /* MODELICA_UTILITY_FUNCTIONS_H */
