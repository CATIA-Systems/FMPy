import os
from itertools import product
from platform import system

import pytest

import fmpy
from fmpy import simulate_fmu
from fmpy.util import download_file, compile_platform_binary, create_cmake_project, visual_c_versions


# some source code FMUs from different vendors
urls = [
    'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/c-code/MapleSim/2016.2/Rectifier/Rectifier.fmu',
    'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/c-code/Dymola/2017/IntegerNetwork1/IntegerNetwork1.fmu',
]

compilers = []

if len(visual_c_versions()) > 0:
    compilers.append('vc')

if fmpy.system in ['linux', 'windows'] and os.system('gcc --version') == 0:
    compilers.append('gcc')

if os.system('clang --version') == 0:
    compilers.append('clang')


@pytest.mark.parametrize('url, compiler', product(urls, compilers))
def test_compile_platform_binary(url, compiler):
    """ Compile the platform binary """

    # add debug info
    if compiler == 'vc':
        compiler_options = '/LDd /Zi'
    elif compiler == 'clang':
        compiler_options = None
    else:
        compiler_options = '-g -fPIC'

    filename = download_file(url)

    compile_platform_binary(filename, compiler_options=compiler_options, compiler=compiler)

    simulate_fmu(filename=filename)


@pytest.mark.parametrize('url', urls)
def notest_cmake(url):
    """ Create a CMake project """

    from subprocess import check_call
    import shutil
    from fmpy.util import visual_c_versions

    try:
        # check if CMake is installed
        check_call(['cmake'])
        cmake_available = True
    except:
        cmake_available = False

    filename = download_file(url)

    model_name, _ = os.path.splitext(filename)

    # clean up
    if os.path.isdir(model_name):
        shutil.rmtree(model_name)

    # create the CMake project
    create_cmake_project(filename, model_name)

    if not cmake_available:
        pytest.skip("CMake is not available.")

    # generate the build system
    cmake_args = ['cmake', '.']

    vc_versions = visual_c_versions()

    if os.name == 'nt':
        if 170 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 17 2022', '-A', 'x64']
        elif 160 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 16 2019', '-A', 'x64']
        elif 150 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 15 2017 Win64']
        elif 140 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 14 2015 Win64']
        elif 120 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 12 2013 Win64']
        elif 110 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 11 2012 Win64']

    check_call(args=cmake_args, cwd=model_name)

    # run the build system
    check_call(args=['cmake', '--build', '.'], cwd=model_name)

    # simulate the FMU
    simulate_fmu(filename=os.path.join(model_name, filename))
