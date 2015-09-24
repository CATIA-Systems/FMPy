
from ctypes import *
from itertools import combinations

import numpy as np

fmi2Component            = c_void_p
fmi2ComponentEnvironment = c_void_p
fmi2FMUstate             = c_void_p
fmi2ValueReference       = c_uint
fmi2Real                 = c_double
fmi2Integer              = c_int
fmi2Boolean              = c_int
fmi2Char                 = c_char
fmi2String               = c_char_p
fmi2Type                 = c_int
fmi2Byte                 = c_char

fmi2Status = c_int

fmi2CallbackLoggerTYPE         = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String)
fmi2CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi2CallbackFreeMemoryTYPE     = CFUNCTYPE(None, c_void_p)
fmi2StepFinishedTYPE           = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2Status)

fmi2ModelExchange = 0
fmi2CoSimulation  = 1

fmi2True  = 1
fmi2False = 0

fmi2StatusKind = c_int
fmi2DoStepStatus       = 0
fmi2PendingStatus      = 1
fmi2LastSuccessfulTime = 2
fmi2Terminated         = 3

calloc          = cdll.msvcrt.calloc
calloc.argtypes = [c_size_t, c_size_t]
calloc.restype  = c_void_p

free = cdll.msvcrt.free
free.argtypes = [c_void_p]

def logger(a, b, c, d, e):
    print a, b, c, d, e

def allocateMemory(nobj, size):
    print "allocateMemory(%d, %d)" % (nobj, size)
    return calloc(nobj, size)

def freeMemory(obj):
    print "free(%d)" % obj
    free(obj)

def stepFinished(componentEnvironment, status):
    print combinations, status

class fmi2CallbackFunctions(Structure):
    _fields_ = [('logger',               fmi2CallbackLoggerTYPE),
                ('allocateMemory',       fmi2CallbackAllocateMemoryTYPE),
                ('freeMemory',           fmi2CallbackFreeMemoryTYPE),
                ('stepFinished',         fmi2StepFinishedTYPE),
                ('componentEnvironment', fmi2ComponentEnvironment)]

callbacks = fmi2CallbackFunctions()
callbacks.logger               = fmi2CallbackLoggerTYPE(logger)
callbacks.allocateMemory       = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
callbacks.stepFinished         = fmi2StepFinishedTYPE(stepFinished)
callbacks.freeMemory           = fmi2CallbackFreeMemoryTYPE(freeMemory)
callbacks.componentEnvironment = None

library = cdll.LoadLibrary('bouncingBall/binaries/win32/bouncingBall.dll')

fmi2Instantiate = getattr(library, 'fmi2Instantiate')
fmi2Instantiate.argtypes = [fmi2String, fmi2Type, fmi2String, fmi2String, POINTER(fmi2CallbackFunctions), fmi2Boolean, fmi2Boolean]
fmi2Instantiate.restype = fmi2ComponentEnvironment

fmi2SetupExperiment          = getattr(library, 'fmi2SetupExperiment')
fmi2SetupExperiment.argtypes = [fmi2Component, fmi2Boolean, fmi2Real, fmi2Real, fmi2Boolean, fmi2Real]
fmi2SetupExperiment.restype  = fmi2Status

fmi2EnterInitializationMode          = getattr(library, 'fmi2EnterInitializationMode')
fmi2EnterInitializationMode.argtypes = [fmi2Component]
fmi2EnterInitializationMode.restype  = fmi2Status

fmi2ExitInitializationMode          = getattr(library, 'fmi2ExitInitializationMode')
fmi2ExitInitializationMode.argtypes = [fmi2Component]
fmi2ExitInitializationMode.restype  = fmi2Status

fmi2DoStep          = getattr(library, 'fmi2DoStep')
fmi2DoStep.argtypes = [fmi2Component, fmi2Real, fmi2Real, fmi2Boolean]
fmi2DoStep.restype  = fmi2Status

fmi2GetReal          = getattr(library, 'fmi2GetReal')
fmi2GetReal.argtypes = [fmi2Component, POINTER(fmi2ValueReference), c_size_t, POINTER(fmi2Real)]
fmi2GetReal.restype  = fmi2Status

fmi2GetBooleanStatus          = getattr(library, 'fmi2GetBooleanStatus')
fmi2GetBooleanStatus.argtypes = [fmi2Component, fmi2StatusKind, POINTER(fmi2Boolean)]
fmi2GetBooleanStatus.restype  = fmi2Status

fmi2Terminate          = getattr(library, 'fmi2Terminate')
fmi2Terminate.argtypes = [fmi2Component]
fmi2Terminate.restype  = fmi2Status

fmi2FreeInstance          = getattr(library, 'fmi2FreeInstance')
fmi2FreeInstance.argtypes = [fmi2Component]
fmi2FreeInstance.restype  = None

c = fmi2Instantiate('bouncingBall', fmi2CoSimulation, '{8c4e810f-3df3-4a00-8276-176fa3c9f003}', '', byref(callbacks), fmi2False, fmi2False)

status = fmi2SetupExperiment(c, fmi2False, 0.0, 0.0, fmi2True, 3.0)

status = fmi2EnterInitializationMode(c)
status = fmi2ExitInitializationMode(c)

step = 1e-2

time = np.linspace(0, 2.5, 251)

vr    = (fmi2ValueReference * 1)(0)
value = (fmi2Real * 1)(0.0)
b     = fmi2Boolean(fmi2False)

height = [0.0]

for t, h in zip(time[1:], np.diff(time)):
    status = fmi2DoStep(c, t, h, fmi2True)
    status = fmi2GetBooleanStatus(c, fmi2Terminated, byref(b))
    status = fmi2GetReal(c, vr, len(vr), value)

    print "%g, %g" % (t, value[0])
    t += step

    height.append(value[0])

status = fmi2Terminate(c)
fmi2FreeInstance(c)

import matplotlib.pyplot as plt

plt.plot(time, height)
plt.show()

pass