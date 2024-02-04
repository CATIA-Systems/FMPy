import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


# build configuration
config = 'Release'
basedir = os.path.abspath(os.path.dirname(__file__))


# RPC-LIB
basedir = os.path.abspath(os.path.dirname(__file__))

rpclib_dir = os.path.join(basedir, 'rpclib-2.3.0').replace('\\', '/')

if not os.path.isdir(rpclib_dir):

    filename = download_file(url='https://github.com/rpclib/rpclib/archive/refs/tags/v2.3.0.tar.gz',
                             checksum='eb9e6fa65e1a79b37097397f60599b93cb443d304fbc0447c50851bc3452fdef')

    print("Extracting %s" % filename)
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall()

    # patch the CMake project to link static against the MSVC runtime
    with open(os.path.join(rpclib_dir, 'CMakeLists.txt'), 'a') as file:
        file.write('''
            
    message(${CMAKE_CXX_FLAGS_RELEASE})
    message(${CMAKE_CXX_FLAGS_DEBUG})
    
    set(CompilerFlags
            CMAKE_CXX_FLAGS
            CMAKE_CXX_FLAGS_DEBUG
            CMAKE_CXX_FLAGS_RELEASE
            CMAKE_C_FLAGS
            CMAKE_C_FLAGS_DEBUG
            CMAKE_C_FLAGS_RELEASE
            )
    foreach(CompilerFlag ${CompilerFlags})
      string(REPLACE "/MD" "/MT" ${CompilerFlag} "${${CompilerFlag}}")
    endforeach()
    
    message(${CMAKE_CXX_FLAGS_RELEASE})
    message(${CMAKE_CXX_FLAGS_DEBUG})
    ''')


# Compilation

if os.name == 'nt':

    for directory, architecture in [('win32', 'Win32'), ('win64', 'x64')]:

        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', directory), ignore_errors=True)

        print(f"Building rpclib for {architecture}...")
        check_call(args=[
            'cmake',
            '-B', rpclib_dir + '/' + directory,
            '-D', 'RPCLIB_MSVC_STATIC_RUNTIME=ON',
            '-D', 'CMAKE_INSTALL_PREFIX=' + os.path.join(rpclib_dir, directory, 'install'),
            '-G', 'Visual Studio 17 2022',
            '-A', architecture,
            rpclib_dir
        ])

        check_call(args=[
            'cmake',
            '--build', os.path.join(rpclib_dir, directory),
            '--target', 'install',
            '--config', config
        ])

        print(f"Building remoting binaries for {directory}...")

        check_call(args=[
            'cmake',
            '-G', 'Visual Studio 17 2022',
            '-A', architecture,
            '-D', 'RPCLIB=' + os.path.join(rpclib_dir, directory, 'install'),
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


        print("Building rpclib...")

        check_call(args=[
            'cmake',
            '-B', os.path.join(rpclib_dir, directory),
            '-D', 'CMAKE_INSTALL_PREFIX=' + os.path.join(rpclib_dir, directory, 'install'),
            '-D', 'CMAKE_POSITION_INDEPENDENT_CODE=ON',
            '-G', 'Unix Makefiles',
            rpclib_dir
        ])

        check_call(args=[
            'cmake',
            '--build', os.path.join(rpclib_dir, directory),
            '--target', 'install',
            '--config', config
        ])


        print("Building remoting binaries...")

        check_call(args=[
            'cmake',
            '-G', 'Unix Makefiles',
            '-B', f'remoting/{directory}',
            '-D', 'RPCLIB=' + os.path.join(rpclib_dir, directory, 'install'),
            f'-DBUILD_32={build_32}',
            'remoting'
        ])

        check_call(['cmake', '--build', f'remoting/{directory}', '--config', config])
