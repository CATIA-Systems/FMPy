import os
import weakref
from ctypes import *
from itertools import count
import fmpy

library_dir, _ = os.path.split(__file__)

logging = cdll.LoadLibrary(os.path.join(library_dir, fmpy.platform, 'logging' + fmpy.sharedLibraryExtension))

_addLoggerProxy = getattr(logging, 'addLoggerProxy')
_addLoggerProxy.argtypes = [c_void_p]  # pointer to a struct whose first field is the logger
_addLoggerProxy.restype = None

# same layout for fmi1CallbackLoggerTYPE and fmi2CallbackLoggerTYPE
_LoggerTYPE = CFUNCTYPE(None, c_void_p, c_char_p, c_int, c_char_p, c_char_p)

# FMI 2.0: key (passed as componentEnvironment) -> (logger, original componentEnvironment)
_fmi2Loggers = {}

# FMI 1.0 has no componentEnvironment: the messages go to the most recently added logger
_fmi1Loggers = {}

_keys = count(1)


def _dispatch(environment, instanceName, status, category, message):
    """ Forward a message formatted by the native proxy to the logger of its callback functions """

    if environment in _fmi2Loggers:
        (logger, _), environment = _fmi2Loggers[environment]
    elif _fmi1Loggers:
        logger, _ = next(reversed(_fmi1Loggers.values()))
    else:
        return

    logger(environment, instanceName, status, category, message)


class _ProxyCallbacks(Structure):
    _fields_ = [('logger', _LoggerTYPE)]


# the native proxy forwards all messages to this callback, which is never freed
_dispatcher = _LoggerTYPE(_dispatch)
_proxyCallbacks = _ProxyCallbacks(_dispatcher)
_addLoggerProxy(byref(_proxyCallbacks))
_logMessage = cast(_proxyCallbacks.logger, c_void_p).value


def addLoggerProxy(functions):
    """ Adds a native proxy function that formats the message string using the variadic arguments that cannot be
    passed to Python with ctypes

    functions  fmi1CallbackFunctions or fmi2CallbackFunctions (or a reference to it created with byref())
    """

    callbacks = getattr(functions, '_obj', functions)

    loggerType = type(callbacks.logger)
    address = cast(callbacks.logger, c_void_p).value

    if address == _logMessage:
        return  # already added

    # keep the Python callback alive after the logger field has been overwritten
    thunk = (callbacks._objects or {}).get('0')

    logger = (loggerType(address), thunk)

    key = next(_keys)

    if any(name == 'componentEnvironment' for name, _ in callbacks._fields_):
        _fmi2Loggers[key] = (logger, callbacks.componentEnvironment)
        callbacks.componentEnvironment = key
        weakref.finalize(callbacks, _fmi2Loggers.pop, key, None)
    else:
        _fmi1Loggers[key] = logger
        weakref.finalize(callbacks, _fmi1Loggers.pop, key, None)

    callbacks.logger = loggerType(_logMessage)
