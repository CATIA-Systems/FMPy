from ctypes import byref, c_char_p
import numpy as np
from fmpy.sundials import SUN_COMM_NULL, SUNErrHandlerFn, SUNErrCode
from fmpy.sundials.nvector_serial import N_VNew_Serial, N_VDestroy_Serial, NV_DATA_S
from fmpy.sundials.sunmatrix_dense import SUNDenseMatrix
from fmpy.sundials.sunlinsol_dense import SUNLinSol_Dense
from fmpy.sundials.sundials_context import SUNContext_Create, SUNContext_PushErrHandler
from fmpy.sundials.cvode import *
from fmpy.sundials.cvode_ls import *


def test_bouncing_ball():
    """ Test CVode with a simple bouncing ball equation """

    # arrays to collect the samples
    time = []
    value = []

    T0 = 0.0
    nx = 2  # number of states (height, velocity)
    nz = 1  # number of event indicators

    def ehfun(line: c_int, func: c_char_p, file: c_char_p, msg: c_char_p, err_code: SUNErrCode, err_user_data: c_void_p, sunctx: SUNContext) -> None:
        print(msg)

    e = SUNErrHandlerFn(ehfun)

    def rhsf(t, y, ydot, user_data):
        x = np.ctypeslib.as_array(NV_DATA_S(y), (2,))
        dx = np.ctypeslib.as_array(NV_DATA_S(ydot), (2,))
        dx[0] = x[1]  # velocity
        dx[1] = -9.81  # gravity
        time.append(t)
        value.append(x[0])
        return 0

    f = CVRhsFn(rhsf)

    def rootf(t, y, gout, user_data):
        x = np.ctypeslib.as_array(NV_DATA_S(y), (nz,))
        gout_ = np.ctypeslib.as_array(gout, (nz,))
        gout_[0] = x[0]
        return 0

    g = CVRootFn(rootf)

    RTOL = 1e-5

    sunctx = SUNContext()

    flag = SUNContext_Create(SUN_COMM_NULL, byref(sunctx))
    assert flag == 0

    abstol = N_VNew_Serial(nx, sunctx)
    abstol_array = np.ctypeslib.as_array(NV_DATA_S(abstol), (nx,))
    abstol_array[:] = RTOL

    y = N_VNew_Serial(nx, sunctx)
    x_ = np.ctypeslib.as_array(NV_DATA_S(y), (nx,))
    x_[0] = 1
    x_[1] = 5

    cvode_mem = CVodeCreate(CV_BDF, sunctx)

    flag = SUNContext_PushErrHandler(sunctx, e, None)
    assert flag == 0

    flag = CVodeInit(cvode_mem, f, T0, y)
    assert flag == 0

    flag = CVodeSVtolerances(cvode_mem, RTOL, abstol)
    assert flag == 0

    flag = CVodeRootInit(cvode_mem, nz, g)
    assert flag == 0

    A = SUNDenseMatrix(nx, nx)

    LS = SUNLinSol_Dense(y, A, sunctx)

    flag = CVodeSetLinearSolver(cvode_mem, LS, A)
    assert flag == 0

    # flag = CVDense(cvode_mem, nx)
    #
    tNext = 2.0
    tret = sunrealtype(0.0)

    while tret.value < 2.0:

        flag = CVode(cvode_mem, tNext, y, byref(tret), CV_NORMAL)

        if flag == CV_ROOT_RETURN:

            rootsfound = (c_int * nz)()

            flag = CVodeGetRootInfo(cvode_mem, rootsfound)
            assert flag == CV_SUCCESS

            if rootsfound[0] == -1:
                x_[1] = -x_[1] * 0.5

            # reset solver
            flag = CVodeReInit(cvode_mem, tret, y)
            assert flag == CV_SUCCESS

        else:
            assert flag == CV_SUCCESS

    # clean up
    CVodeFree(byref(c_void_p(cvode_mem)))
    N_VDestroy_Serial(y)

    # import matplotlib.pyplot as plt
    #
    # plt.plot(time, value, '.-')
    # plt.show()
