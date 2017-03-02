# noinspection PyPep8

import sys
from enum import Enum
from ctypes import *
import _ctypes


# determine the platform
if sys.platform == 'win32':
    platform = 'win'
    sharedLibraryExtension = '.dll'
    calloc = cdll.msvcrt.calloc
    free = cdll.msvcrt.free
    freeLibrary = _ctypes.FreeLibrary
elif sys.platform == 'linux':
    platform = 'linux'
    sharedLibraryExtension = '.so'
    from ctypes.util import find_library
    libc = CDLL(find_library("c"))
    calloc = libc.calloc
    free = libc.free
    freeLibrary = _ctypes.dlclose
else:
    raise Exception("Usupported platfrom: " + sys.platform)

calloc.argtypes = [c_size_t, c_size_t]
calloc.restype = c_void_p

free.argtypes = [c_void_p]

if sys.maxsize > 2**32:
    platform += '64'
else:
    platform += '32'

class FMIType(Enum):
    MODEL_EXCHANGE = 0
    CO_SIMULATION = 1

def fmu_info(filename):
    """ Read the FMI version and supported interfaces from an FMU without extracting it """

    from lxml import etree
    import zipfile

    zf = zipfile.ZipFile(filename, 'r')
    md = zf.open('modelDescription.xml')
    tree = etree.parse(md)
    root = tree.getroot()
    version = root.get('fmiVersion')

    return version, ['Co-Simulation']
