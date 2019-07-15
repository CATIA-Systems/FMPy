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

        from subprocess import check_call
        import shutil
        from fmpy import platform

        try:
            # check if CMake is installed
            check_call(['cmake'])
            cmake_available = True
        except:
            cmake_available = False

        for fmu in self.fmus:

            download_file(self.url + fmu)

            filename = os.path.basename(fmu)

            model_name, _ = os.path.splitext(filename)

            # clean up
            if os.path.isdir(model_name):
                shutil.rmtree(model_name)

            # create the CMake project
            create_cmake_project(filename, model_name)

            if not cmake_available:
                continue  # skip compilation

            if platform == 'win32':
                generator = 'Visual Studio 15 2017'
            elif platform == 'win64':
                generator = 'Visual Studio 15 2017 Win64'
            else:
                generator = 'Unix Makefiles'

            # generate the build system
            check_call(args=['cmake', '-G', generator, '.'], cwd=model_name)

            # run the build system
            check_call(args=['cmake', '--build', '.'], cwd=model_name)

            # simulate the FMU
            result = simulate_fmu(filename=os.path.join(model_name, filename))

            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
