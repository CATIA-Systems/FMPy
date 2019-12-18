from ctypes import cdll
import os
from fmpy import sharedLibraryExtension

library_dir, _ = os.path.split(__file__)

# load SUNDIALS shared libraries
sundials_nvecserial     = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_nvecserial'     + sharedLibraryExtension))
sundials_sunmatrixdense = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_sunmatrixdense' + sharedLibraryExtension))
sundials_sunlinsoldense = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_sunlinsoldense' + sharedLibraryExtension))
sundials_cvode          = cdll.LoadLibrary(os.path.join(library_dir, 'sundials_cvode'          + sharedLibraryExtension))
