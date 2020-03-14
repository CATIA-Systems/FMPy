import os
from ctypes import *
from .. import platform, sharedLibraryExtension
from ..fmi2 import fmi2CallbackFunctions


library_dir, _ = os.path.split(__file__)

logging = cdll.LoadLibrary(os.path.join(library_dir, platform, 'logging' + sharedLibraryExtension))

""" Adds a native proxy function that formats the message string using the variadic arguments that cannot be 
passed to Python with ctypes """
addLoggerProxy = getattr(logging, 'addLoggerProxy')
addLoggerProxy.argtypes = [POINTER(fmi2CallbackFunctions)]
addLoggerProxy.restype = None
