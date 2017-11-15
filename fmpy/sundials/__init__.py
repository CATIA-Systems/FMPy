""" Interface to the SUNDIALS libraries """

from ctypes import *
import os
import numpy as np
from fmpy import platform, sharedLibraryExtension

# types
realtype = c_double
booleantype = c_int

library_dir, _ = os.path.split(__file__)
library_dir = os.path.join(library_dir, platform)

# load SUNDIALS shared libraries
sundials_nvecserial = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_nvecserial' + sharedLibraryExtension))
sundials_cvode = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_cvode' + sharedLibraryExtension))


# struct _N_VectorContent_Serial {
#   long int length;
#   booleantype own_data;
#   realtype *data;
# };
class _N_VectorContent_Serial(Structure):
    _fields_ = [('content',  c_long),
                ('own_data', booleantype),
                ('data',     POINTER(realtype))]


# struct _generic_N_Vector {
#   void *content;
#   struct _generic_N_Vector_Ops *ops;
# };
class _generic_N_Vector(Structure):
    _fields_ = [('content',               c_void_p),
                ('_generic_N_Vector_Ops', c_void_p)]

# typedef struct _N_VectorContent_Serial *N_VectorContent_Serial;
N_VectorContent_Serial = POINTER(_N_VectorContent_Serial)

N_Vector = POINTER(_generic_N_Vector)

N_VNew_Serial = getattr(sundials_nvecserial, 'N_VNew_Serial')
N_VNew_Serial.argtypes = [c_long]
N_VNew_Serial.restype = N_Vector

# void N_VDestroy_Serial(N_Vector v)
N_VDestroy_Serial = getattr(sundials_nvecserial, 'N_VDestroy_Serial')
N_VDestroy_Serial.argtypes = [N_Vector]
N_VDestroy_Serial.restype = None

# void *CVodeCreate(int lmm, int iter)
CVodeCreate = getattr(sundials_cvode, 'CVodeCreate')
CVodeCreate.argtypes = [c_int, c_int]
CVodeCreate.restype = c_void_p

# typedef int (*CVRhsFn)(realtype t, N_Vector y, N_Vector ydot, void *user_data);
CVRhsFn = CFUNCTYPE(c_int, realtype, N_Vector, N_Vector, c_void_p)

# typedef int (*CVRootFn)(realtype t, N_Vector y, realtype *gout, void *user_data);
CVRootFn = CFUNCTYPE(c_int, realtype, N_Vector, POINTER(realtype), c_void_p)

# int CVodeInit(void *cvode_mem, CVRhsFn f, realtype t0, N_Vector y0)
CVodeInit = getattr(sundials_cvode, 'CVodeInit')
CVodeInit.argtypes = [c_void_p, CVRhsFn, realtype, N_Vector]
CVodeInit.restype = c_int

# int CVodeSetMaxStep(void *cvode_mem, realtype hmax);
CVodeSetMaxStep = getattr(sundials_cvode, 'CVodeSetMaxStep')
CVodeSetMaxStep.argtypes = [c_void_p, realtype]
CVodeSetMaxStep.restype = c_int

# void CVodeFree(void **cvode_mem)
CVodeFree = getattr(sundials_cvode, 'CVodeFree')
CVodeFree.argtypes = [POINTER(c_void_p)]
CVodeFree.restype = None

# int CVodeRootInit(void *cvode_mem, int nrtfn, CVRootFn g)
CVodeRootInit = getattr(sundials_cvode, 'CVodeRootInit')
CVodeRootInit.argtypes = [c_void_p, c_int, CVRootFn]
CVodeRootInit.restype = c_int

# int CVodeReInit(void *cvode_mem, realtype t0, N_Vector y0)
CVodeReInit = getattr(sundials_cvode, 'CVodeReInit')
CVodeReInit.argtypes = [c_void_p, realtype, N_Vector]
CVodeReInit.restype = c_int

# int CVodeSVtolerances(void *cvode_mem, realtype reltol, N_Vector abstol)
CVodeSVtolerances = getattr(sundials_cvode, 'CVodeSVtolerances')
CVodeSVtolerances.argtypes = [c_void_p, realtype, N_Vector]
CVodeSVtolerances.restype = c_int

# int CVDense(void *cvode_mem, long int N)
CVDense = getattr(sundials_cvode, 'CVDense')
CVDense.argtypes = [c_void_p, c_long]
CVDense.restype = c_int

#  int CVode(void *cvode_mem, realtype tout, N_Vector yout, realtype *tret, int itask)
CVode = getattr(sundials_cvode, 'CVode')
CVode.argtypes = [c_void_p, realtype, N_Vector, POINTER(realtype), c_int]
CVode.restype = c_int

# constants
CV_BDF    = 2
CV_NEWTON = 2
CV_NORMAL = 1


# macros

# #define NV_CONTENT_S(v)  ( (N_VectorContent_Serial)(v->content) )
def NV_CONTENT_S(v):
    return cast(v.contents.content, N_VectorContent_Serial)


# #define NV_DATA_S(v)     ( NV_CONTENT_S(v)->data )
def NV_DATA_S(v):
    return NV_CONTENT_S(v).contents.data


class CVodeSolver(object):

    def __init__(self,
                 fmu,
                 numberOfContinuousStates,
                 numberOfEventIndicators,
                 startTime,
                 stopTime,
                 maxStep=None,
                 relativeTolerance=1e-5):

        self.fmu = fmu

        self.discrete = numberOfContinuousStates == 0

        if self.discrete:
            # insert a dummy state
            self.nx = 1
        else:
            self.nx = numberOfContinuousStates

        self.nz = numberOfEventIndicators

        if maxStep is None:
            # perform at least 50 steps
            maxStep = (stopTime - startTime) / 50.

        self.x      = N_VNew_Serial(self.nx)
        self.abstol = N_VNew_Serial(self.nx)

        self.px      = NV_DATA_S(self.x)
        self.pabstol = NV_DATA_S(self.abstol)

        # initialize
        if self.discrete:
            x = np.ctypeslib.as_array(self.px, (self.nx,))
            x[:] = 1.0
        else:
            self.fmu.getContinuousStates(self.px, self.nx)

        abstol = np.ctypeslib.as_array(self.pabstol, (self.nx,))
        abstol[:] = relativeTolerance

        self.cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON)

        # add function pointers as members to save them from GC
        self.f_ = CVRhsFn(self.f)
        self.g_ = CVRootFn(self.g)

        flag = CVodeInit(self.cvode_mem, self.f_, startTime, self.x)

        flag = CVodeRootInit(self.cvode_mem, self.nz, self.g_)

        flag = CVodeSVtolerances(self.cvode_mem, relativeTolerance, self.abstol)

        flag = CVDense(self.cvode_mem, self.nx)

        flag = CVodeSetMaxStep(self.cvode_mem, maxStep)

    def f(self, t, y, ydot, user_data):
        """ Right-hand-side function """

        self.fmu.setTime(t)

        if self.discrete:
            dx = np.ctypeslib.as_array(NV_DATA_S(ydot), (self.nx,))
            dx[:] = 0.0
        else:
            self.fmu.setContinuousStates(NV_DATA_S(y), self.nx)
            self.fmu.getDerivatives(NV_DATA_S(ydot), self.nx)
        return 0

    def g(self, t, y, gout, user_data):
        """ Root function """

        self.fmu.setTime(t)

        if not self.discrete:
            self.fmu.setContinuousStates(NV_DATA_S(y), self.nx)

        self.fmu.getEventIndicators(gout, self.nz)

        return 0

    def step(self, t, tNext):

        if not self.discrete:
            self.fmu.getContinuousStates(self.px, self.nx)

        tret = realtype(0.0)

        # perform one step
        flag = CVode(self.cvode_mem, tNext, self.x, byref(tret), CV_NORMAL)

        stateEvent = flag > 0

        return stateEvent, tret.value

    def reset(self, time):

        if not self.discrete:
            self.fmu.getContinuousStates(self.px, self.nx)

        # reset the solver
        flag = CVodeReInit(self.cvode_mem, time, self.x)

    def __del__(self):
        # clean up
        CVodeFree(byref(c_void_p(self.cvode_mem)))
