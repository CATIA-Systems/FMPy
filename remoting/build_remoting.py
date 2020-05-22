import os
import tarfile
import shutil
from subprocess import check_call
from fmpy.util import download_file


url = 'https://github.com/rpclib/rpclib/archive/v2.2.1.tar.gz'
checksum = 'ceef2c521a1712035bc64d1bd5e3b2c7de16a1d856cbbeadd000ae318c96463f'

# build configuration
config = 'Release'

download_file(url, checksum)

filename = os.path.basename(url)

basedir = os.path.dirname(__file__)

source_dir = 'rpclib-2.2.1'

rpclib_dir = os.path.join(basedir, source_dir).replace('\\', '/')

shutil.rmtree(source_dir, ignore_errors=True)

print("Extracting %s" % filename)
with tarfile.open(filename, 'r:gz') as tar:
    tar.extractall()

path = os.path.dirname(__file__)

print("Building RPCLIB...")
for bitness, generator in [('win32', 'Visual Studio 15 2017'), ('win64', 'Visual Studio 15 2017 Win64')]:

    cmake_args = [
        'cmake',
        '-B', source_dir + '/' + bitness,
        '-D', 'RPCLIB_MSVC_STATIC_RUNTIME=ON',
        '-D', 'CMAKE_INSTALL_PREFIX=' + source_dir + '/' + bitness + '/rpc',
        '-G', generator,
        source_dir
    ]

    check_call(args=cmake_args)
    check_call(args=['cmake', '--build', source_dir + '/' + bitness, '--target', 'install', '--config', config])

print("Building server.exe...")
check_call(['cmake', '-G', 'Visual Studio 15 2017', '-D', 'RPCLIB=' + rpclib_dir + '/win32/rpc', '-B', 'server/build', 'server'])
check_call(['cmake', '--build', 'server/build', '--config', config])

print("Building client.dll...")
check_call(['cmake', '-G', 'Visual Studio 15 2017 Win64', '-D', 'RPCLIB=' + rpclib_dir + '/win64/rpc', '-B', 'client/build', 'client'])
check_call(['cmake', '--build', 'client/build', '--config', config])
