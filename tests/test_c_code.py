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
        """ Compile directly """

        for fmu in self.fmus:
            download_file(self.url + fmu)

            filename = os.path.basename(fmu)

            # compile in-place
            result = simulate_fmu(filename=filename, use_source_code=True)
            self.assertIsNotNone(result)

            # add binary to FMU
            compile_platform_binary(filename)

            result = simulate_fmu(filename=filename)
            self.assertIsNotNone(result)

    def test_cmake(self):
        """ Create a CMake project """

        from subprocess import call, list2cmdline
        import shutil

        cmake_available = False

        try:
            res = call(['cmake'])
            cmake_available = True
        except OSError as e:
            pass

        for fmu in self.fmus:
            download_file(self.url + fmu)

            filename = os.path.basename(fmu)

            model_name, _ = os.path.splitext(filename)

            # clean up
            if os.path.isdir(model_name):
                shutil.rmtree(model_name)

            # create an empty directory
            os.makedirs(model_name)

            # create the CMake project
            create_cmake_project(filename, model_name)

            if cmake_available and os.name == 'nt':

                params = [
                    'cd', model_name, '&',
                    'cmake', '-G', 'Visual Studio 14 2015 Win64', '.', '&',  # create a Visual Studio 2015 solution
                    r'%VS140COMNTOOLS%..\..\VC\vcvarsall.bat ', '&',         # set VS environment variables
                    'msbuild', model_name + '.sln'                           # build the solution
                ]

                print(list2cmdline(params))

                # create and build the solution
                status = call(params, shell=True)

                self.assertEqual(0, status)

                # simulate the FMU
                result = simulate_fmu(filename=os.path.join(model_name, filename))

                self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
