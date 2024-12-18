from .libraries import sundials_cvode
from .sundials_matrix import *
from .sundials_linearsolver import *

# #include <sundials/sundials_direct.h>
# #include <sundials/sundials_iterative.h>
# #include <sundials/sundials_linearsolver.h>
# #include <sundials/sundials_matrix.h>
# #include <sundials/sundials_nvector.h>
#
# #ifdef __cplusplus  /* wrapper to enable C++ usage */
# extern "C" {
# #endif
#
#
# /*=================================================================
#   CVLS Constants
#   =================================================================*/
#
# #define CVLS_SUCCESS          0
# #define CVLS_MEM_NULL        -1
# #define CVLS_LMEM_NULL       -2
# #define CVLS_ILL_INPUT       -3
# #define CVLS_MEM_FAIL        -4
# #define CVLS_PMEM_NULL       -5
# #define CVLS_JACFUNC_UNRECVR -6
# #define CVLS_JACFUNC_RECVR   -7
# #define CVLS_SUNMAT_FAIL     -8
# #define CVLS_SUNLS_FAIL      -9
#
#
# /*=================================================================
#   CVLS user-supplied function prototypes
#   =================================================================*/
#
# typedef int (*CVLsJacFn)(realtype t, N_Vector y, N_Vector fy,
#                          SUNMatrix Jac, void *user_data,
#                          N_Vector tmp1, N_Vector tmp2, N_Vector tmp3);
#
# typedef int (*CVLsPrecSetupFn)(realtype t, N_Vector y, N_Vector fy,
#                                booleantype jok, booleantype *jcurPtr,
#                                realtype gamma, void *user_data);
#
# typedef int (*CVLsPrecSolveFn)(realtype t, N_Vector y, N_Vector fy,
#                                N_Vector r, N_Vector z, realtype gamma,
#                                realtype delta, int lr, void *user_data);
#
# typedef int (*CVLsJacTimesSetupFn)(realtype t, N_Vector y,
#                                    N_Vector fy, void *user_data);
#
# typedef int (*CVLsJacTimesVecFn)(N_Vector v, N_Vector Jv, realtype t,
#                                  N_Vector y, N_Vector fy,
#                                  void *user_data, N_Vector tmp);
#
#
# /*=================================================================
#   CVLS Exported functions
#   =================================================================*/
#
# SUNDIALS_EXPORT int CVodeSetLinearSolver(void *cvode_mem,
#                                          SUNLinearSolver LS,
#                                          SUNMatrix A);
CVodeSetLinearSolver = getattr(sundials_cvode, 'CVodeSetLinearSolver')
CVodeSetLinearSolver.argtypes = [c_void_p, SUNLinearSolver, SUNMatrix]
CVodeSetLinearSolver.restype = c_int
#
#
# /*-----------------------------------------------------------------
#   Optional inputs to the CVLS linear solver interface
#   -----------------------------------------------------------------*/
#
# SUNDIALS_EXPORT int CVodeSetJacFn(void *cvode_mem, CVLsJacFn jac);
# SUNDIALS_EXPORT int CVodeSetMaxStepsBetweenJac(void *cvode_mem,
#                                                long int msbj);
# SUNDIALS_EXPORT int CVodeSetEpsLin(void *cvode_mem, realtype eplifac);
# SUNDIALS_EXPORT int CVodeSetPreconditioner(void *cvode_mem,
#                                            CVLsPrecSetupFn pset,
#                                            CVLsPrecSolveFn psolve);
# SUNDIALS_EXPORT int CVodeSetJacTimes(void *cvode_mem,
#                                      CVLsJacTimesSetupFn jtsetup,
#                                      CVLsJacTimesVecFn jtimes);
#
# /*-----------------------------------------------------------------
#   Optional outputs from the CVLS linear solver interface
#   -----------------------------------------------------------------*/
#
# SUNDIALS_EXPORT int CVodeGetLinWorkSpace(void *cvode_mem,
#                                          long int *lenrwLS,
#                                          long int *leniwLS);
# SUNDIALS_EXPORT int CVodeGetNumJacEvals(void *cvode_mem,
#                                         long int *njevals);
# SUNDIALS_EXPORT int CVodeGetNumPrecEvals(void *cvode_mem,
#                                          long int *npevals);
# SUNDIALS_EXPORT int CVodeGetNumPrecSolves(void *cvode_mem,
#                                           long int *npsolves);
# SUNDIALS_EXPORT int CVodeGetNumLinIters(void *cvode_mem,
#                                         long int *nliters);
# SUNDIALS_EXPORT int CVodeGetNumLinConvFails(void *cvode_mem,
#                                             long int *nlcfails);
# SUNDIALS_EXPORT int CVodeGetNumJTSetupEvals(void *cvode_mem,
#                                               long int *njtsetups);
# SUNDIALS_EXPORT int CVodeGetNumJtimesEvals(void *cvode_mem,
#                                            long int *njvevals);
# SUNDIALS_EXPORT int CVodeGetNumLinRhsEvals(void *cvode_mem,
#                                            long int *nfevalsLS);
# SUNDIALS_EXPORT int CVodeGetLastLinFlag(void *cvode_mem,
#                                         long int *flag);
# SUNDIALS_EXPORT char *CVodeGetLinReturnFlagName(long int flag);
