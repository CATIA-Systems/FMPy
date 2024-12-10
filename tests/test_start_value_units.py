import pytest
from fmpy import *
from fmpy.util import download_test_file


if platform not in ['win32', 'win64']:
    pytest.skip(reason="FMU only available for Windows", allow_module_level=True)

download_test_file('2.0', 'CoSimulation', 'Dymola', '2017', 'Rectifier', 'Rectifier.fmu')


def test_start_value_units():

    start_values = {
        'IdealDiode1.T': 294.15,  # no unit
        'IdealDiode2.T': (295.15, None),  # no unit as tuple
        'IdealDiode3.T': (296.15, 'K'),  # base unit
        'IdealDiode4.T': (24, 'degC'),  # display unit
    }

    result = simulate_fmu('Rectifier.fmu', start_values=start_values, output=['IdealDiode1.T', 'IdealDiode2.T', 'IdealDiode3.T', 'IdealDiode4.T'])

    assert 294.15 == result['IdealDiode1.T'][0]
    assert 295.15, result['IdealDiode2.T'][0]
    assert 296.15, result['IdealDiode3.T'][0]
    assert 297.15, result['IdealDiode4.T'][0]

def test_illegal_tuple():

    with pytest.raises(Exception) as exception_info:
        simulate_fmu('Rectifier.fmu', start_values={'IdealDiode1.T': (294.15,)})

    assert str(exception_info.value) == 'The start value for variable IdealDiode1.T must be a scalar value or a tuple (<value>, {<unit>|<display_unit>}) but was "(294.15,)".'

def test_no_base_unit():

    with pytest.raises(Exception) as exception_info:
        simulate_fmu('Rectifier.fmu', start_values={'IdealDiode1.off': (True, '?')})

    assert str(exception_info.value) == 'Variable IdealDiode1.off has no unit but the unit "?" was specified for its start value.'

def test_illegal_unit():

    with pytest.raises(Exception) as exception_info:
        simulate_fmu('Rectifier.fmu', start_values={'IdealDiode1.T': (294.15, 'm2')})

    assert str(exception_info.value) == 'The unit "m2" of the start value for variable IdealDiode1.T is not defined.'
