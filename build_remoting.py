import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


url = 'https://github.com/rpclib/rpclib/archive/refs/tags/v2.3.0.tar.gz'
checksum = 'eb9e6fa65e1a79b37097397f60599b93cb443d304fbc0447c50851bc3452fdef'

# build configuration
config = 'Release'

download_file(url, checksum)

filename = os.path.basename(url)

basedir = os.path.abspath(os.path.dirname(__file__))

source_dir = 'rpclib-2.3.0'

rpclib_dir = os.path.join(basedir, source_dir).replace('\\', '/')

# clean up
shutil.rmtree(source_dir, ignore_errors=True)

print("Extracting %s" % filename)
with tarfile.open(filename, 'r:gz') as tar:
    tar.extractall()

if os.name == 'nt':

    # patch the CMake project to link static against the MSVC runtime
    with open(os.path.join(source_dir, 'CMakeLists.txt'), 'a') as file:
        # Append 'hello' at the end of file
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

    for bitness, generator in [('win32', 'Visual Studio 15 2017'), ('win64', 'Visual Studio 15 2017 Win64')]:

        # clean up
        shutil.rmtree(os.path.join(basedir, 'remoting', bitness), ignore_errors=True)

        print("Building rpclib...")

        check_call(args=[
            'cmake',
            '-B', source_dir + '/' + bitness,
            '-D', 'RPCLIB_MSVC_STATIC_RUNTIME=ON',
            '-D', 'CMAKE_INSTALL_PREFIX=' + source_dir + '/' + bitness + '/install',
            '-G', generator,
            source_dir
        ])

        check_call(args=['cmake', '--build', source_dir + '/' + bitness, '--target', 'install', '--config', config])

        print("Building remoting binaries...")

        check_call(args=[
            'cmake',
            '-B', 'remoting/' + bitness,
            '-G', generator,
            '-D', 'RPCLIB=' + rpclib_dir + '/' + bitness + '/install',
            '-B', 'remoting/' + bitness, 'remoting'
        ])

        check_call(['cmake', '--build', 'remoting/' + bitness, '--config', config])

else:

    # clean up
    shutil.rmtree(os.path.join(basedir, 'remoting', 'linux64'), ignore_errors=True)

    print("Building rpclib...")

    check_call(args=[
        'cmake',
        '-B', source_dir + '/linux64',
        '-D', 'CMAKE_INSTALL_PREFIX=' + source_dir + '/linux64' + '/install',
        '-D', 'CMAKE_POSITION_INDEPENDENT_CODE=ON',
        '-G', 'Unix Makefiles',
        source_dir
    ])

    check_call(args=['cmake', '--build', source_dir + '/linux64', '--target', 'install', '--config', config])

    print("Building remoting binaries...")

    check_call(args=[
        'cmake',
        '-B', 'remoting/' + 'linux64',
        '-G', 'Unix Makefiles',
        '-D', 'RPCLIB=' + rpclib_dir + '/linux64/install',
        '-B', 'remoting/linux64', 'remoting'
    ])

    check_call(['cmake', '--build', 'remoting/linux64', '--config', config])
