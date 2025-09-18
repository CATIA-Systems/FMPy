from ctypes import cdll
from pathlib import Path
from fmpy import sharedLibraryExtension, platform_tuple


library_dir = Path(__file__).parent

if platform_tuple == 'x86_64-darwin':
    library_dir = library_dir / 'aarch64_darwin'
else:
    library_dir = library_dir / platform_tuple

# load SUNDIALS shared libraries
sundials_nvecserial     = cdll.LoadLibrary(str(library_dir / f'sundials_nvecserial{sharedLibraryExtension}'))
sundials_sunmatrixdense = cdll.LoadLibrary(str(library_dir / f'sundials_sunmatrixdense{sharedLibraryExtension}'))
sundials_sunlinsoldense = cdll.LoadLibrary(str(library_dir / f'sundials_sunlinsoldense{sharedLibraryExtension}'))
sundials_core           = cdll.LoadLibrary(str(library_dir / f'sundials_core{sharedLibraryExtension}'))
sundials_cvode          = cdll.LoadLibrary(str(library_dir / f'sundials_cvode{sharedLibraryExtension}'))
