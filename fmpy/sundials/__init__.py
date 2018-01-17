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

# Return flags
CV_SUCCESS = 0


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

# typedef void (*CVErrHandlerFn)(int error_code, const char *module, const char *function, char *msg, void *user_data);
CVErrHandlerFn = CFUNCTYPE(None, c_int, c_char_p, c_char_p, c_char_p, c_void_p)

# typedef int (*CVRhsFn)(realtype t, N_Vector y, N_Vector ydot, void *user_data);
CVRhsFn = CFUNCTYPE(c_int, realtype, N_Vector, N_Vector, c_void_p)

# typedef int (*CVRootFn)(realtype t, N_Vector y, realtype *gout, void *user_data);
CVRootFn = CFUNCTYPE(c_int, realtype, N_Vector, POINTER(realtype), c_void_p)

# int CVodeSetErrHandlerFn(void *cvode_mem, CVErrHandlerFn ehfun, void *eh_data);
CVodeSetErrHandlerFn = getattr(sundials_cvode, 'CVodeSetErrHandlerFn')
CVodeSetErrHandlerFn.argtypes = [c_void_p, CVErrHandlerFn, c_void_p]
CVodeSetErrHandlerFn.restype = c_int

# int CVodeInit(void *cvode_mem, CVRhsFn f, realtype t0, N_Vector y0)
CVodeInit = getattr(sundials_cvode, 'CVodeInit')
CVodeInit.argtypes = [c_void_p, CVRhsFn, realtype, N_Vector]
CVodeInit.restype = c_int

# int CVodeSetMaxStep(void *cvode_mem, realtype hmax);
CVodeSetMaxStep = getattr(sundials_cvode, 'CVodeSetMaxStep')
CVodeSetMaxStep.argtypes = [c_void_p, realtype]
CVodeSetMaxStep.restype = c_int

# int CVodeSetMaxNumSteps(void *cvode_mem, long int mxsteps);
CVodeSetMaxNumSteps = getattr(sundials_cvode, 'CVodeSetMaxNumSteps')
CVodeSetMaxNumSteps.argtypes = [c_void_p, c_long]
CVodeSetMaxNumSteps.restype = c_int

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
    """ Interface to the CVode solver """

    def __init__(self,
                 nx, nz, get_x, set_x, get_dx, get_z, set_time,
                 startTime,
                 maxStep=float('inf'),
                 relativeTolerance=1e-5,
                 maxNumSteps=500):
        """
        Parameters:
            nx                  number of continuous states
            nz                  number of event indicators
            get_x               callback function to get the continuous states
            set_x               callback function to set the continuous states
            get_dx              callback function to get the derivatives
            get_z               callback function to get the event indicators
            set_time            callback function to set the time
            startTime           start time for the integration
            maxStep             maximum absolute value of step size allowed
            relativeTolerance   relative tolerance
            maxNumSteps         maximum number of internal steps to be taken by the solver in its attempt to reach tout
        """

        self.get_x = get_x
        self.set_x = set_x
        self.get_dx = get_dx
        self.get_z = get_z
        self.set_time = set_time

        self.discrete = nx == 0

        if self.discrete:
            # insert a dummy state
            self.nx = 1
        else:
            self.nx = nx

        self.nz = nz

        self.x      = N_VNew_Serial(self.nx)
        self.abstol = N_VNew_Serial(self.nx)

        self.px      = NV_DATA_S(self.x)
        self.pabstol = NV_DATA_S(self.abstol)

        # initialize
        if self.discrete:
            x = np.ctypeslib.as_array(self.px, (self.nx,))
            x[:] = 1.0
        else:
            self.get_x(self.px, self.nx)

        abstol = np.ctypeslib.as_array(self.pabstol, (self.nx,))
        abstol[:] = relativeTolerance

        self.cvode_mem = CVodeCreate(CV_BDF, CV_NEWTON)

        # add function pointers as members to save them from GC
        self.f_ = CVRhsFn(self.f)
        self.g_ = CVRootFn(self.g)

        assert CVodeInit(self.cvode_mem, self.f_, startTime, self.x) == CV_SUCCESS

        assert CVodeRootInit(self.cvode_mem, self.nz, self.g_) == CV_SUCCESS

        assert CVodeSVtolerances(self.cvode_mem, relativeTolerance, self.abstol) == CV_SUCCESS

        assert CVDense(self.cvode_mem, self.nx) == CV_SUCCESS

        assert CVodeSetMaxStep(self.cvode_mem, maxStep) == CV_SUCCESS

        assert CVodeSetMaxNumSteps(self.cvode_mem, maxNumSteps) == CV_SUCCESS

    def ehfun(self, error_code, module, function, msg,  user_data):
        """ Error handler function """
        print("[%s] %s" % (module.decode("utf-8"), msg.decode("utf-8")))

    def f(self, t, y, ydot, user_data):
        """ Right-hand-side function """

        self.set_time(t)

        if self.discrete:
            dx = np.ctypeslib.as_array(NV_DATA_S(ydot), (self.nx,))
            dx[:] = 0.0
        else:
            self.set_x(NV_DATA_S(y), self.nx)
            self.get_dx(NV_DATA_S(ydot), self.nx)
        return 0

    def g(self, t, y, gout, user_data):
        """ Root function """

        self.set_time(t)

        if not self.discrete:
            self.set_x(NV_DATA_S(y), self.nx)

        self.get_z(gout, self.nz)

        return 0

    def step(self, t, tNext):

        if not self.discrete:
            self.get_x(self.px, self.nx)

        tret = realtype(0.0)

        # perform one step
        flag = CVode(self.cvode_mem, tNext, self.x, byref(tret), CV_NORMAL)

        stateEvent = flag > 0

        return stateEvent, tret.value

    def reset(self, time):

        if not self.discrete:
            self.get_x(self.px, self.nx)

        # reset the solver
        flag = CVodeReInit(self.cvode_mem, time, self.x)

    def __del__(self):
        # clean up
        CVodeFree(byref(c_void_p(self.cvode_mem)))
