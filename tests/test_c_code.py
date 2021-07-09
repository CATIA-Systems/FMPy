from fmpy import simulate_fmu

import unittest
from fmpy.util import download_file
import os
from fmpy.util import compile_platform_binary, create_cmake_project


class CCodeTest(unittest.TestCase):
    """ Test compilation of source code FMUs from various vendors """

    url = 'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/c-code/'

    fmus = [
        'MapleSim/2016.2/Rectifier/Rectifier.fmu',
        'Dymola/2017/IntegerNetwork1/IntegerNetwork1.fmu',
    ]

    def test_compile(self):
        """ Compile the platform binary """

        for fmu in self.fmus:

            filename = download_file(self.url + fmu)

            compile_platform_binary(filename)

            result = simulate_fmu(filename=filename)
            self.assertIsNotNone(result)

    def test_cmake(self):
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

        for fmu in self.fmus:

            filename = download_file(self.url + fmu)

            model_name, _ = os.path.splitext(filename)

            # clean up
            if os.path.isdir(model_name):
                shutil.rmtree(model_name)

            # create the CMake project
            create_cmake_project(filename, model_name)

            if not cmake_available:
                continue  # skip compilation

            # generate the build system
            cmake_args = ['cmake', '.']

            vc_versions = visual_c_versions()

            if os.name == 'nt':
                if 160 in vc_versions:
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

            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
