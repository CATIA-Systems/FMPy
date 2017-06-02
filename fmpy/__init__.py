# noinspection PyPep8

import sys
import os
from ctypes import *
import _ctypes


# determine the platform
if sys.platform == 'win32':
    platform = 'win'
    sharedLibraryExtension = '.dll'
    calloc = cdll.msvcrt.calloc
    free = cdll.msvcrt.free
    freeLibrary = _ctypes.FreeLibrary
elif sys.platform.startswith('linux'):
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

# FMI type constants
MODEL_EXCHANGE = 0
CO_SIMULATION = 1


def supported_platforms(filename):
    """ Get the platforms supported by the FMU without extracting it """

    import zipfile

    platforms = []

    # open the FMU
    with zipfile.ZipFile(filename, 'r') as zf:

        # get the supported platforms
        names = zf.namelist()

        # check for the C-sources
        for name in names:
            head, tail = os.path.split(name)
            if head == 'sources' and tail.endswith('.c'):
                platforms.append('c-code')
                break

        # check for *.dylib on Mac
        for name in names:
            head, tail = os.path.split(name)
            if head == 'binaries/darwin64' and tail.endswith('.dylib'):
                platforms.append('darwin64')
                break

        # check for *.so on Linux
        for platform in ['linux32', 'linux64']:
            for name in names:
                head, tail = os.path.split(name)
                if head == 'binaries/' + platform and tail.endswith('.so'):
                    platforms.append(platform)
                    break

        # check for *.dll on Windows
        for platform in ['win32', 'win64']:
            for name in names:
                head, tail = os.path.split(name)
                if head == 'binaries/' + platform and tail.endswith('.dll'):
                    platforms.append(platform)
                    break

    return platforms


def fmi_info(filename):
    """ Read the FMI version and supported FMI types from the FMU without extracting it """

    from lxml import etree
    import zipfile

    fmi_types = []

    # open the FMU
    with zipfile.ZipFile(filename, 'r') as zf:

        # read the model description
        md = zf.open('modelDescription.xml')
        tree = etree.parse(md)
        root = tree.getroot()
        fmi_version = root.get('fmiVersion')

        # get the supported FMI types
        if fmi_version == '1.0':

            if root.find('Implementation') is not None:
                fmi_types.append('CoSimulation')
            else:
                fmi_types.append('ModelExchange')

        elif fmi_version == '2.0':

            if root.find('ModelExchange') is not None:
                fmi_types.append('ModelExchange')

            if root.find('CoSimulation') is not None:
                fmi_types.append('CoSimulation')

        else:
            raise Exception("Unsupported FMI version %s" % fmi_version)

    return fmi_version, fmi_types

# make the functions available in the fmpy module
from .model_description import read_model_description
from .simulation import simulate_fmu
