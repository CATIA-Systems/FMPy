""" Simulate Functional Mock-up Units (FMUs) in Python """

import sys
import os
from ctypes import *
import _ctypes

__version__ = '0.2.10'


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


def supported_platforms(filename):
    """ Get the platforms supported by the FMU without extracting it

    Parameters:
        filename    filename of the FMU or directory with extracted FMU

    Returns:
        platforms   a list of supported platforms supported by the FMU
    """

    import zipfile

    platforms = []

    # get the files within the FMU
    if os.path.isdir(filename):
        names = []
        for dirpath, _, filenames in os.walk(filename):
            for name in filenames:
                abspath = os.path.join(dirpath, name)
                names.append(os.path.relpath(abspath, start=filename).replace('\\', '/'))
    else:
        with zipfile.ZipFile(filename, 'r') as zf:
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
        if head in {'binaries/darwin64', 'binaries/x86_64-darwin'} and tail.endswith('.dylib'):
            platforms.append('darwin64')
            break

    # check for *.so on Linux
    for bitness, architecture in [('32', 'i686'), ('64', 'x86_64')]:
        for name in names:
            head, tail = os.path.split(name)
            if head in {'binaries/linux' + bitness, 'binaries/' + architecture + '-linux'} and tail.endswith('.so'):
                platforms.append('linux' + bitness)
                break

    # check for *.dll on Windows
    for bitness, architecture in [('32', 'i686'), ('64', 'x86_64')]:
        for name in names:
            head, tail = os.path.split(name)
            if head in {'binaries/win' + bitness, 'binaries/' + architecture + '-windows'} and tail.endswith('.dll'):
                platforms.append('win' + bitness)
                break

    return platforms


def fmi_info(filename):
    """ Read the FMI version and supported FMI types from the FMU without extracting it

    Parameters:
        filename      filename of the FMU

    Returns:
        fmi_version   FMI version as a string ('1.0' or '2.0')
        fmi_types     list of supported FMI types ('CoSimulation', 'ModelExchange')
    """

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


def extract(filename, unzipdir=None):
    """ Extract a ZIP archive to a temporary directory

    Parameters:
        filename    filename of the ZIP archive
        unzipdir    target directory (None: create temporary directory)

    Returns:
        unzipdir    path to the directory that contains the extracted files
    """

    from tempfile import mkdtemp
    import zipfile

    if unzipdir is None:
        unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform.startswith('win'):
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    # extract the archive
    with zipfile.ZipFile(filename, 'r') as zf:
        zf.extractall(unzipdir)

    return unzipdir


def dump(filename):
    """ Print the model information and variables of an FMU

    Parameters:
        filename    filename of the FMU
    """

    from .util import fmu_info
    print(fmu_info(filename))


# make the functions available in the fmpy module
from .model_description import read_model_description
from .simulation import simulate_fmu
