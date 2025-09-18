from ctypes import POINTER
from .libraries import sundials_core
from .sundials_types import *

# /* -----------------------------------------------------------------
#  * Programmer(s): Cody J. Balos @ LLNL
#  * -----------------------------------------------------------------
#  * SUNDIALS Copyright Start
#  * Copyright (c) 2002-2025, Lawrence Livermore National Security
#  * and Southern Methodist University.
#  * All rights reserved.
#  *
#  * See the top-level LICENSE and NOTICE files for details.
#  *
#  * SPDX-License-Identifier: BSD-3-Clause
#  * SUNDIALS Copyright End
#  * -----------------------------------------------------------------
#  * SUNDIALS context class. A context object holds data that all
#  * SUNDIALS objects in a simulation share. It is thread-safe provided
#  * that each thread has its own context object.
#  * ----------------------------------------------------------------*/
#
# #ifndef _SUNDIALS_CONTEXT_H
# #define _SUNDIALS_CONTEXT_H
#
# #include <sundials/priv/sundials_context_impl.h>
#
# #ifdef __cplusplus /* wrapper to enable C++ usage */
# extern "C" {
# #endif
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_Create(SUNComm comm, SUNContext* sunctx_out);
SUNContext_Create = getattr(sundials_core, 'SUNContext_Create')
SUNContext_Create.argtypes = [SUNComm, POINTER(SUNContext)]
SUNContext_Create.restype = c_int
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_GetLastError(SUNContext sunctx);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_PeekLastError(SUNContext sunctx);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_PushErrHandler(SUNContext sunctx, SUNErrHandlerFn err_fn,
#                                      void* err_user_data);
SUNContext_PushErrHandler = getattr(sundials_core, 'SUNContext_PushErrHandler')
SUNContext_PushErrHandler.argtypes = [SUNContext, SUNErrHandlerFn, c_void_p]
SUNContext_PushErrHandler.restype = c_int
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_PopErrHandler(SUNContext sunctx);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_ClearErrHandlers(SUNContext sunctx);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_GetProfiler(SUNContext sunctx, SUNProfiler* profiler);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_SetProfiler(SUNContext sunctx, SUNProfiler profiler);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_GetLogger(SUNContext sunctx, SUNLogger* logger);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_SetLogger(SUNContext sunctx, SUNLogger logger);
#
# SUNDIALS_EXPORT
# SUNErrCode SUNContext_Free(SUNContext* ctx);
#
# #ifdef __cplusplus
# }
#
# #endif
# #endif
