
import sys
from ctypes import *
import _ctypes

# determine the platform
if sys.platform.startswith('win'):
    platform = 'win'
    system = 'windows'
    sharedLibraryExtension = '.dll'
elif sys.platform.startswith('linux'):
    platform = 'linux'
    system = 'linux'
    sharedLibraryExtension = '.so'
elif sys.platform.startswith('darwin'):
    platform = 'darwin'
    system = 'darwin'
    sharedLibraryExtension = '.dylib'
else:
    raise Exception("Unsupported platform: " + sys.platform)


# load the C library functions
if sys.platform.startswith('win'):
    calloc = cdll.msvcrt.calloc
    realloc = cdll.msvcrt.realloc
    free = cdll.msvcrt.free
    freeLibrary = _ctypes.FreeLibrary
else:
    from ctypes.util import find_library
    libc = CDLL(find_library("c"))
    calloc = libc.calloc
    realloc = libc.realloc
    free = libc.free
    freeLibrary = _ctypes.dlclose

calloc.argtypes = [c_size_t, c_size_t]
calloc.restype = c_void_p

realloc.argtypes = [c_void_p, c_size_t]
realloc.restype = c_void_p

free.argtypes = [c_void_p]
free.restype = None

if sys.maxsize > 2**32:
    platform += '64'
    architecture = 'x86_64'
else:
    platform += '32'
    architecture = 'i686'

platform_tuple = architecture + '-' + system
