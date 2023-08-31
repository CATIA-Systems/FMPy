import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


# build configuration
config = 'Release'
basedir = os.path.abspath(os.path.dirname(__file__))

if os.name == 'nt':

    for directory, architecture in [('win32', 'Win32'), ('win64', 'x64')]:

        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', directory), ignore_errors=True)

        print(f"Building remoting binaries for {directory}...")

        check_call(args=[
            'cmake',
            '-G', 'Visual Studio 17 2022',
            '-A', architecture,
            '-B', 'remoting/' + directory,
            'remoting'
        ])

        check_call(['cmake', '--build', 'remoting/' + directory, '--config', config])

else:
    import platform

    if platform.system() == 'Linux':
        compilation = [('linux64', 'OFF'), ('linux32', 'ON')]
    else:
        compilation = [('darwin64', 'OFF')]

    for directory, build_32 in compilation:
        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', directory), ignore_errors=True)
        print("Building remoting binaries...")

        check_call(args=[
            'cmake',
            '-G', 'Unix Makefiles',
            '-B', f'remoting/{directory}',
            f'-DBUILD_32={build_32}',
            'remoting'
        ])

        check_call(['cmake', '--build', f'remoting/{directory}', '--config', config])
