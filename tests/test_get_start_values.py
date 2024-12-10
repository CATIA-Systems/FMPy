import pytest
from fmpy import platform
from fmpy.util import download_test_file, get_start_values


def test_get_start_values():

    if platform.startswith('win'):
        fmi_versions = ['2.0']  # quick fix until FMUs are available
    elif platform.startswith(('darwin', 'linux')):
        fmi_versions = ['2.0']
    else:
        pytest.fail('Platform not supported')

    for fmi_version in fmi_versions:

        for fmi_type in ['CoSimulation', 'ModelExchange']:

            download_test_file(fmi_version, fmi_type, 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

            start_values = get_start_values('CoupledClutches.fmu')

            assert start_values['CoupledClutches1_freqHz'] == '0.2'
