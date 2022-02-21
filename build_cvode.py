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
shutil.rmtree('sundials-5.3.0', ignore_errors=True)

filename = download_file(url='https://github.com/LLNL/sundials/releases/download/v5.3.0/sundials-5.3.0.tar.gz',
                         checksum='88dff7e11a366853d8afd5de05bf197a8129a804d9d4461fb64297f1ef89bca7')

with tarfile.open(filename, "r:gz") as tar:
    tar.extractall()

for platform, cmake_options, platform_tuple in generators:

    os.makedirs(f'sundials-5.3.0/{platform}/static')

    # build CVode as static library
    check_call([
        'cmake',
        '-D', 'BUILD_ARKODE=OFF',
        '-D', 'BUILD_CVODES=OFF',
        '-D', 'BUILD_IDA=OFF',
        '-D', 'BUILD_IDAS=OFF',
        '-D', 'BUILD_KINSOL=OFF',
        '-D', 'BUILD_SHARED_LIBS=OFF',
        '-D', f'CMAKE_INSTALL_PREFIX=sundials-5.3.0/{platform}/static/install',
        '-D', 'CMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
        '-D', 'EXAMPLES_ENABLE_C=OFF',
        '-S', 'sundials-5.3.0',
        '-B', f'sundials-5.3.0/{platform}/static'
    ] + cmake_options)

    check_call(['cmake', '--build', f'sundials-5.3.0/{platform}/static', '--target', 'install', '--config', configuration])

    os.makedirs(f'sundials-5.3.0/{platform}/dynamic')

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
        '-D', f'CMAKE_INSTALL_PREFIX=sundials-5.3.0/{platform}/dynamic/install',
        '-D', 'CMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
        '-S', 'sundials-5.3.0',
        '-B', f'sundials-5.3.0/{platform}/dynamic'
    ] + cmake_options)

    check_call(['cmake', '--build', f'sundials-5.3.0/{platform}/dynamic', '--target', 'install', '--config', configuration])

    sundials_binary_dir = os.path.join('fmpy', 'sundials', platform_tuple)

    os.makedirs(sundials_binary_dir, exist_ok=True)

    os.path.join('sundials-5.3.0', platform, 'dynamic', 'install', 'sundials_cvode' + sharedLibraryExtension)

    for name in ['sundials_cvode', 'sundials_nvecserial', 'sundials_sunlinsoldense', 'sundials_sunmatrixdense']:
        src = os.path.join('sundials-5.3.0', platform, 'dynamic', 'install', 'lib', sl_prefix + name + sl_suffix)
        dst = os.path.join(sundials_binary_dir, name + sl_suffix)
        shutil.copy(src, dst)
