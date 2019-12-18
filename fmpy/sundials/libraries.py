from ctypes import cdll
import os
from fmpy import sharedLibraryExtension, platform_tuple

library_dir, _ = os.path.split(__file__)

# load SUNDIALS shared libraries
sundials_nvecserial     = cdll.LoadLibrary(os.path.join(library_dir, platform_tuple, 'sundials_nvecserial'     + sharedLibraryExtension))
sundials_sunmatrixdense = cdll.LoadLibrary(os.path.join(library_dir, platform_tuple, 'sundials_sunmatrixdense' + sharedLibraryExtension))
sundials_sunlinsoldense = cdll.LoadLibrary(os.path.join(library_dir, platform_tuple, 'sundials_sunlinsoldense' + sharedLibraryExtension))
sundials_cvode          = cdll.LoadLibrary(os.path.join(library_dir, platform_tuple, 'sundials_cvode'          + sharedLibraryExtension))
