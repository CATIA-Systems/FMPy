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
for build_dir in ['cswrapper/build', 'sundials-5.3.0', sundials_binary_dir, 'fmpy/logging/build']:
    if os.path.isdir(build_dir):
        shutil.rmtree(build_dir)

url = 'https://github.com/LLNL/sundials/releases/download/v5.3.0/sundials-5.3.0.tar.gz'
checksum = '88dff7e11a366853d8afd5de05bf197a8129a804d9d4461fb64297f1ef89bca7'

filename = os.path.basename(url)

download_file(url, checksum)

# response = requests.get(url)
#
# with open(filename, 'wb') as f:
#     f.write(response.content)

with tarfile.open(filename, "r:gz") as tar:
    tar.extractall()

os.mkdir('sundials-5.3.0/static')

# build CVode as static library
check_call([
    'cmake',
    '-DBUILD_ARKODE=OFF',
    '-DBUILD_CVODES=OFF',
    '-DBUILD_IDA=OFF',
    '-DBUILD_IDAS=OFF',
    '-DBUILD_KINSOL=OFF',
    '-DBUILD_SHARED_LIBS=OFF',
    '-DCMAKE_INSTALL_PREFIX=sundials-5.3.0/static/install',
    '-DCMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
    '-DEXAMPLES_ENABLE_C=OFF',
    '-G', generator,
    '-S', 'sundials-5.3.0',
    '-B', 'sundials-5.3.0/static'
])

check_call(['cmake', '--build', 'sundials-5.3.0/static', '--target', 'install', '--config', 'Release'])

# build CVode as dynamic library
check_call([
    'cmake',
    '-DBUILD_ARKODE=OFF',
    '-DBUILD_CVODES=OFF',
    '-DBUILD_IDA=OFF',
    '-DBUILD_IDAS=OFF',
    '-DBUILD_KINSOL=OFF',
    '-DBUILD_STATIC_LIBS=OFF',
    '-DEXAMPLES_ENABLE_C=OFF',
    '-DCMAKE_INSTALL_PREFIX=sundials-5.3.0/dynamic/install',
    '-DCMAKE_USER_MAKE_RULES_OVERRIDE=../OverrideMSVCFlags.cmake',
    '-G', generator,
    '-S', 'sundials-5.3.0',
    '-B', 'sundials-5.3.0/dynamic'
])

check_call(['cmake', '--build', 'sundials-5.3.0/dynamic', '--target', 'install', '--config', 'Release'])

os.mkdir(sundials_binary_dir)

os.path.join('sundials-5.3.0', 'dynamic', 'install', 'sundials_cvode' + sharedLibraryExtension)

for name in ['sundials_cvode', 'sundials_nvecserial', 'sundials_sunlinsoldense', 'sundials_sunmatrixdense']:
    src = os.path.join('sundials-5.3.0', 'dynamic', 'install', 'lib', sl_prefix + name + sl_suffix)
    dst = os.path.join(sundials_binary_dir, name + sl_suffix)
    shutil.copy(src, dst)

# build cswrapper
os.mkdir('cswrapper/build')

check_call([
    'cmake',
    '-DCVODE_INSTALL_DIR=../sundials-5.3.0/static/install',
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
