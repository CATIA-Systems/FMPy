import shutil

from fmpy import platform, sharedLibraryExtension
import os
from subprocess import check_call


if os.name == 'nt':
    generators = [
        ('win32', 'Visual Studio 15 2017'),
        ('win64', 'Visual Studio 15 2017 Win64')
    ]
else:
    generators = [(platform, 'Unix Makefiles')]

for p, generator in generators:

    build_dir = 'fmpy/fmucontainer/%s' % p

    shutil.rmtree(build_dir, ignore_errors=True)
    os.mkdir(build_dir)

    check_call([
        'cmake',
        '-G', generator,
        '-S', 'fmpy/fmucontainer',
        '-B', build_dir
    ])

    check_call(['cmake', '--build', build_dir, '--config', 'Release'])
