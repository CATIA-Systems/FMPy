from fmpy import sharedLibraryExtension, platform
from fmpy import platform_tuple as current_platform_tuple
from fmpy.util import download_file
import tarfile
import os
import shutil
from subprocess import check_call


configuration = 'Release'

if os.name == 'nt':
    generators = [
        ('win32', ['-G', 'Visual Studio 17 2022', '-A', 'Win32'], 'i686-windows'),
        ('win64', ['-G', 'Visual Studio 17 2022', '-A', 'x64'], 'x86_64-windows')
    ]
    sl_prefix = ''
    sl_suffix = sharedLibraryExtension
else:
    generators = [(platform, ['-G', 'Unix Makefiles'], current_platform_tuple)]
    sl_prefix = 'lib'
    sl_suffix = sharedLibraryExtension


# clean up
shutil.rmtree('sundials-7.5.0', ignore_errors=True)

filename = download_file(
    url='https://github.com/LLNL/sundials/releases/download/v7.5.0/sundials-7.5.0.tar.gz',
    checksum='089ac659507def738b7a65b574ffe3a900d38569e3323d9709ebed3e445adecc'
)

with tarfile.open(filename, "r:gz") as tar:
    tar.extractall()

for platform, cmake_options, platform_tuple in generators:

    os.makedirs(f'sundials-7.5.0/{platform}/dynamic')

    # build CVode as dynamic library
    check_call([
        'cmake',
        '-D', 'BUILD_ARKODE=OFF',
        '-D', 'BUILD_CVODES=OFF',
        '-D', 'BUILD_IDA=OFF',
        '-D', 'BUILD_IDAS=OFF',
        '-D', 'BUILD_KINSOL=OFF',
        '-D', 'BUILD_STATIC_LIBS=OFF',
        '-D', 'EXAMPLES_ENABLE_C=OFF',
        '-D', f'CMAKE_INSTALL_PREFIX=sundials-7.5.0/{platform}/dynamic/install',
        '-D', 'CMAKE_POLICY_DEFAULT_CMP0091=NEW',
        '-D', 'CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded',
        '-D', 'CMAKE_OSX_ARCHITECTURES=arm64;x86_64',
        '-S', 'sundials-7.5.0',
        '-B', f'sundials-7.5.0/{platform}/dynamic'
   ] + cmake_options)

    check_call(['cmake', '--build', f'sundials-7.5.0/{platform}/dynamic', '--target', 'install', '--config', configuration])

    sundials_binary_dir = os.path.join('..', 'src', 'fmpy', 'sundials', platform_tuple)

    os.makedirs(sundials_binary_dir, exist_ok=True)

    for name in ['sundials_core', 'sundials_cvode', 'sundials_nvecserial', 'sundials_sunlinsoldense', 'sundials_sunmatrixdense']:
        lib_dir = 'bin' if os.name == 'nt' else 'lib'
        src = os.path.join('sundials-7.5.0', platform, 'dynamic', 'install', lib_dir, sl_prefix + name + sl_suffix)
        dst = os.path.join(sundials_binary_dir, name + sl_suffix)
        shutil.copy(src, dst)
