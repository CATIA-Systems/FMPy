import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


# build configuration
config = 'Debug'
basedir = os.path.abspath(os.path.dirname(__file__))

if os.name == 'nt':

    for bitness, architecture in [('win32', 'Win32'), ('win64', 'x64')]:

        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', bitness), ignore_errors=True)

        print(f"Building remoting binaries for {bitness}...")

        check_call(args=[
            'cmake',
            '-B', 'remoting/' + bitness,
            '-G', 'Visual Studio 17 2022',
            '-A', architecture,
            '-B', 'remoting/' + bitness,
            'remoting'
        ])

        check_call(['cmake', '--build', 'remoting/' + bitness, '--config', config])

else:

    # clean up
    shutil.rmtree(os.path.join(basedir, 'remoting', 'linux64'), ignore_errors=True)

    print("Building remoting binaries...")

    check_call(args=[
        'cmake',
        '-B', 'remoting/' + 'linux64',
        '-G', 'Unix Makefiles',
        '-D', 'RPCLIB=' + os.path.join(rpclib_dir, 'linux64', 'install'),
        '-B', 'remoting/linux64', 'remoting'
    ])

    check_call(['cmake', '--build', 'remoting/linux64', '--config', config])
