from fmpy import platform_tuple, sharedLibraryExtension
from fmpy.util import download_file
import tarfile
import os
import shutil
from subprocess import check_call


if os.name == 'nt':
    generator = 'Visual Studio 15 2017 Win64'
    sl_prefix = ''
    sl_suffix = sharedLibraryExtension
else:
    generator = 'Unix Makefiles'
    sl_prefix = 'lib'
    sl_suffix = sharedLibraryExtension

sundials_binary_dir = os.path.join('fmpy', 'sundials', platform_tuple)

# clean up
for build_dir in ['cswrapper/build', 'cvode-5.3.0', sundials_binary_dir, 'fmpy/logging/build']:
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

url = 'https://computing.llnl.gov/projects/sundials/download/cvode-5.3.0.tar.gz'
checksum = 'd7ff8e77bb2a59cf8143de30f05a2651c2b4d29b586f8003f9187bf9e5a7da6e'

filename = os.path.basename(url)

download_file(url, checksum)

# response = requests.get(url)
#
# with open(filename, 'wb') as f:
#     f.write(response.content)

with tarfile.open(filename, "r:gz") as tar:
    tar.extractall()

os.mkdir('cvode-5.3.0/static')

# build CVode as static library
check_call([
    'cmake',
    '-DEXAMPLES_ENABLE_C=OFF',
    '-DBUILD_SHARED_LIBS=OFF',
    '-DCMAKE_INSTALL_PREFIX=cvode-5.3.0/static/install',
    '-DCMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
    '-G', generator,
    '-S', 'cvode-5.3.0',
    '-B', 'cvode-5.3.0/static'
])

check_call(['cmake', '--build', 'cvode-5.3.0/static', '--target', 'install', '--config', 'Release'])

# build CVode as dynamic library
check_call([
    'cmake',
    '-DEXAMPLES_ENABLE_C=OFF',
    '-DBUILD_STATIC_LIBS=OFF',
    '-DCMAKE_INSTALL_PREFIX=cvode-5.3.0/dynamic/install',
    '-DCMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
    '-G', generator,
    '-S', 'cvode-5.3.0',
    '-B', 'cvode-5.3.0/dynamic'
])

check_call(['cmake', '--build', 'cvode-5.3.0/dynamic', '--target', 'install', '--config', 'Release'])

os.mkdir(sundials_binary_dir)

os.path.join('cvode-5.3.0', 'dynamic', 'install', 'sundials_cvode' + sharedLibraryExtension)

for name in ['sundials_cvode', 'sundials_nvecserial', 'sundials_sunlinsoldense', 'sundials_sunmatrixdense']:
    src = os.path.join('cvode-5.3.0', 'dynamic', 'install', 'lib', sl_prefix + name + sl_suffix)
    dst = os.path.join(sundials_binary_dir, name + sl_suffix)
    shutil.copy(src, dst)

# build cswrapper
os.mkdir('cswrapper/build')

check_call([
    'cmake',
    '-DCVODE_INSTALL_DIR=../cvode-5.3.0/static/install',
    '-G', generator,
    '-S', 'cswrapper',
    '-B', 'cswrapper/build'
])

check_call(['cmake', '--build', 'cswrapper/build', '--config', 'Release'])

# build logging callback
os.mkdir('fmpy/logging/build')

check_call([
    'cmake',
    '-G', generator,
    '-S', 'fmpy/logging',
    '-B', 'fmpy/logging/build'
])

check_call(['cmake', '--build', 'fmpy/logging/build', '--config', 'Release'])
