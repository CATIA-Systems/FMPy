from fmpy import sharedLibraryExtension, platform
from fmpy import platform_tuple as current_platform_tuple
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


for platform, cmake_options, platform_tuple in generators:

    build_dir = f'src/{platform}'

    shutil.rmtree(build_dir, ignore_errors=True)

    check_call([
        'cmake',
        '-D', f'CVODE_INSTALL_DIR=../sundials-5.3.0/{platform}/static/install',
        '-S', 'src',
        '-B', build_dir
    ] + cmake_options)

    check_call(['cmake', '--build', build_dir, '--config', configuration])
