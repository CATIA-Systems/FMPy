import os
from ctypes import *
from .. import platform, sharedLibraryExtension

library_dir, _ = os.path.split(__file__)

logging = cdll.LoadLibrary(os.path.join(library_dir, platform, 'logging' + sharedLibraryExtension))

""" Adds a native proxy function that formats the message string using the variadic arguments that cannot be 
passed to Python with ctypes """
addLoggerProxy = getattr(logging, 'addLoggerProxy')
addLoggerProxy.argtypes = [c_void_p]  # pointer to fmi1CallbackFunctions or fmi2CallbackFunctions
addLoggerProxy.restype = None
