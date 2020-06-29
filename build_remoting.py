from fmpy import sharedLibraryExtension, extract
from fmpy.util import download_file
import os
import shutil
from subprocess import check_call


# clean up
for p in ['rpclib-2.2.1', 'remoting/client/build', 'remoting/server/build']:
    if os.path.exists(p):
        shutil.rmtree(p)

for f in ['fmpy/remoting/client.dll', 'fmpy/remoting/server.exe']:
    if os.path.exists(f):
        os.remove(f)

rpclib_url = 'https://github.com/rpclib/rpclib/archive/v2.2.1.zip'
rpclib_checksum = '70f10b59f0eb303ccee4a9dda32e6ed898783be9a539d32b43e6fcb4430dce0c'
rpclib_filename = os.path.basename(rpclib_url)

download_file(rpclib_url, rpclib_checksum)

extract(rpclib_filename, '.')

# root = os.path.dirname(__file__)

# build RPCLIB for win32
check_call([
    'cmake',
    '-DCMAKE_INSTALL_PREFIX=rpclib-2.2.1/win32/install',
    '-DRPCLIB_MSVC_STATIC_RUNTIME=ON',
    '-G', 'Visual Studio 15 2017',
    '-S', 'rpclib-2.2.1',
    '-B', 'rpclib-2.2.1/win32'
])

check_call(['cmake', '--build', 'rpclib-2.2.1/win32', '--target', 'install', '--config', 'Release'])

# build RPCLIB for win64
check_call([
    'cmake',
    '-DCMAKE_INSTALL_PREFIX=rpclib-2.2.1/win64/install',
    '-DRPCLIB_MSVC_STATIC_RUNTIME=ON',
    '-G', 'Visual Studio 15 2017 Win64',
    '-S', 'rpclib-2.2.1',
    '-B', 'rpclib-2.2.1/win64'
])

check_call(['cmake', '--build', 'rpclib-2.2.1/win64', '--target', 'install', '--config', 'Release'])

print('####' + str([
    'cmake',
    '-DRPCLIB=' + os.path.abspath('rpclib-2.2.1/win32/install').replace('\\', '/'),
    '-G', 'Visual Studio 15 2017',
    '-S', 'remoting/server',
    '-B', 'remoting/server/build'
]))

# build server.exe
check_call([
    'cmake',
    '-DRPCLIB=' + os.path.abspath('rpclib-2.2.1/win32/install').replace('\\', '/'),
    '-G', 'Visual Studio 15 2017',
    '-S', 'remoting/server',
    '-B', 'remoting/server/build'
])

check_call(['cmake', '--build', 'remoting/server/build', '--config', 'Release'])

# build client.exe
check_call([
    'cmake',
    '-DRPCLIB=' + os.path.abspath('rpclib-2.2.1/win64/install').replace('\\', '/'),
    '-G', 'Visual Studio 15 2017 Win64',
    '-S', 'remoting/client',
    '-B', 'remoting/client/build'
])

check_call(['cmake', '--build', 'remoting/client/build', '--config', 'Release'])
