""" Interface to the SUNDIALS libraries """

import numpy as np
from .cvode import *
from .cvode_ls import *
from .nvector_serial import *
from .sundials_linearsolver import *
from .sundials_matrix import *
from .sundials_nvector import *
from .sundials_types import *
from .sundials_version import *
from .sunlinsol_dense import *
from .sunmatrix_dense import *


def _assert_version():
    major = c_int()
    minor = c_int()
    patch = c_int()
    len = 8
    label = create_string_buffer(len)
    status = SUNDIALSGetVersionNumber(byref(major), byref(minor), byref(patch), label, len)
    assert status == 0
    assert major.value == 5


_assert_version()


class CVodeSolver(object):
    """ Interface to the CVode solver """

    def __init__(self,
                 nx, nz, get_x, set_x, get_dx, get_z, set_time, input,
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
        self.input = input
        self.error_info = None

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

        self.cvode_mem = CVodeCreate(CV_BDF)

        # add function pointers as members to save them from GC
        self.f_ = CVRhsFn(self.f)
        self.g_ = CVRootFn(self.g)
        self.ehfun_ = CVErrHandlerFn(self.ehfun)

        assert CVodeInit(self.cvode_mem, self.f_, startTime, self.x) == CV_SUCCESS

        assert CVodeSVtolerances(self.cvode_mem, relativeTolerance, self.abstol) == CV_SUCCESS

        assert CVodeRootInit(self.cvode_mem, self.nz, self.g_) == CV_SUCCESS

        self.A = SUNDenseMatrix(self.nx, self.nx)

        self.LS = SUNLinSol_Dense(self.x, self.A)

        assert CVodeSetLinearSolver(self.cvode_mem, self.LS, self.A) == CV_SUCCESS

        assert CVodeSetMaxStep(self.cvode_mem, maxStep) == CV_SUCCESS

        assert CVodeSetMaxNumSteps(self.cvode_mem, maxNumSteps) == CV_SUCCESS

        assert CVodeSetNoInactiveRootWarn(self.cvode_mem) == CV_SUCCESS

        assert CVodeSetErrHandlerFn(self.cvode_mem, self.ehfun_, None) == CV_SUCCESS

    def ehfun(self, error_code, module, function, msg,  user_data):
        """ Error handler function """
        self.error_info = (error_code, module.decode("utf-8"), function.decode("utf-8"), msg.decode("utf-8"))

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
        self.input.apply(t)

        if not self.discrete:
            self.set_x(NV_DATA_S(y), self.nx)

        self.get_z(gout, self.nz)

        return 0

    def step(self, t, tNext):

        if not self.discrete:
            # get the states
            self.get_x(self.px, self.nx)

        tret = realtype(0.0)

        # perform one step
        flag = CVode(self.cvode_mem, tNext, self.x, byref(tret), CV_NORMAL)

        if not self.discrete:
            # set the states
            self.set_x(self.px, self.nx)

        roots_found = np.zeros(shape=(self.nz,), dtype=np.int32)

        if flag == CV_ROOT_RETURN:
            p_roots_found = np.ctypeslib.as_ctypes(roots_found)
            assert CVodeGetRootInfo(self.cvode_mem, p_roots_found) == CV_SUCCESS
        elif flag < 0:
            raise RuntimeError("CVode error (code %s) in module %s, function %s: %s" % self.error_info)

        return flag > 0, roots_found, tret.value

    def reset(self, time):

        if not self.discrete:
            self.get_x(self.px, self.nx)

        # reset the solver
        flag = CVodeReInit(self.cvode_mem, time, self.x)

    def __del__(self):
        # clean up
        CVodeFree(byref(c_void_p(self.cvode_mem)))
