# Test compilation of source code FMUs from various vendors

import pytest
from fmpy import simulate_fmu
from fmpy.util import download_file
import os
from fmpy.util import compile_platform_binary, create_cmake_project


urls = [
    'https://github.com/modelica/fmi-cross-check/raw/refs/heads/master/fmus/2.0/cs/c-code/MapleSim/2021.2/Rectifier/Rectifier.fmu',
    'https://github.com/CATIA-Systems/dymola-fmi-compatibility/raw/refs/heads/main/2025x,%202024-10-11/CoupledClutches_fmi2_Cvode.fmu',
    # 'https://github.com/CATIA-Systems/dymola-fmi-compatibility/raw/refs/heads/main/2025x,%202024-10-11/CoupledClutches_fmi3_Cvode.fmu',
]


@pytest.mark.parametrize('url', urls)
def test_compile(url):
    """ Compile the platform binary """

    # add debug info
    if os.name == 'nt':
        compiler_options = '/LDd /Zi'
    else:
        compiler_options = '-g -fPIC'

    filename = download_file(url)

    compile_platform_binary(filename, compiler_options=compiler_options)

    result = simulate_fmu(filename=filename)

    assert result is not None


@pytest.mark.parametrize('url', urls)
def test_cmake(url):
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
        return  # skip compilation

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
    result = simulate_fmu(filename=os.path.join(model_name, filename))

    assert result is not None
