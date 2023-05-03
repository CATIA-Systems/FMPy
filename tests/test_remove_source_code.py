from fmpy import supported_platforms

from fmpy.util import remove_source_code, download_test_file, download_file


def test_remove_source_code():

    filename = download_file('https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win64/Dymola/2019FD01/BooleanNetwork1/BooleanNetwork1.fmu')

    assert 'c-code' in supported_platforms(filename)

    remove_source_code(filename)

    assert 'c-code' not in supported_platforms(filename)
