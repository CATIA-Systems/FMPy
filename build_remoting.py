import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


# build configuration
config = 'Debug'

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

if os.name == 'nt':

    for bitness, generator in [('win32', 'Visual Studio 15 2017'), ('win64', 'Visual Studio 15 2017 Win64')]:

        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', bitness), ignore_errors=True)

        print(f"Building rpclib for {bitness}...")

        check_call(args=[
            'cmake',
            '-B', rpclib_dir + '/' + bitness,
            '-D', 'RPCLIB_MSVC_STATIC_RUNTIME=ON',
            '-D', 'CMAKE_INSTALL_PREFIX=' + os.path.join(rpclib_dir, bitness, 'install'),
            '-G', generator,
            rpclib_dir
        ])

        check_call(args=[
            'cmake',
            '--build', os.path.join(rpclib_dir, bitness),
            '--target', 'install',
            '--config', config
        ])

        print(f"Building remoting binaries for {bitness}...")

        check_call(args=[
            'cmake',
            '-B', 'remoting/' + bitness,
            '-G', generator,
            '-D', 'RPCLIB=' + os.path.join(rpclib_dir, bitness, 'install'),
            '-B', 'remoting/' + bitness,
            'remoting'
        ])

        check_call(['cmake', '--build', 'remoting/' + bitness, '--config', config])

else:

    # clean up
    shutil.rmtree(os.path.join(basedir, 'remoting', 'linux64'), ignore_errors=True)

    print("Building rpclib...")

    check_call(args=[
        'cmake',
        '-B', os.path.join(rpclib_dir, 'linux64'),
        '-D', 'CMAKE_INSTALL_PREFIX=' + os.path.join(rpclib_dir, 'linux64', 'install'),
        '-D', 'CMAKE_POSITION_INDEPENDENT_CODE=ON',
        '-G', 'Unix Makefiles',
        rpclib_dir
    ])

    check_call(args=[
        'cmake',
        '--build', os.path.join(rpclib_dir, 'linux64'),
        '--target', 'install',
        '--config', config
    ])

    print("Building remoting binaries...")

    check_call(args=[
        'cmake',
        '-B', 'remoting/' + 'linux64',
        '-G', 'Unix Makefiles',
        '-D', 'RPCLIB=' + os.path.join(rpclib_dir, 'linux64', 'install'),
        '-B', 'remoting/linux64', 'remoting'
    ])

    check_call(['cmake', '--build', 'remoting/linux64', '--config', config])
