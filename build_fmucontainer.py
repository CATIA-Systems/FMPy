import shutil

from fmpy import platform, sharedLibraryExtension
import os
from subprocess import check_call


if os.name == 'nt':
    generators = [
        ('win32', 'Visual Studio 16 2019', 'Win32'),
        ('win64', 'Visual Studio 16 2019', 'x64')
    ]
else:
    generators = [(platform, 'Unix Makefiles', None)]

for p, generator, architecture in generators:

    build_dir = 'fmpy/fmucontainer/%s' % p

    shutil.rmtree(build_dir, ignore_errors=True)
    os.mkdir(build_dir)

    command = [
        'cmake',
        '-G', generator,
        '-S', 'fmpy/fmucontainer',
        '-B', build_dir
    ]

    if architecture is not None:
        command += ['-A', architecture]

    check_call(command)

    check_call(['cmake', '--build', build_dir, '--config', 'Release'])
