# Test the validation of model description

import pytest
from fmpy import read_model_description, simulate_fmu, platform_tuple
from fmpy.model_description import ValidationError
from fmpy.util import download_file, download_test_file


def test_validate_derivatives():

    filename = download_file(
        url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
        checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f'
    )

    with pytest.raises(ValidationError) as exception_info:
        read_model_description(filename, validate=True, validate_variable_names=False)

    assert exception_info.value.problems[0] == 'The unit "" of variable "inputs" (line 183) is not defined.'

def test_validate_variable_names():

    filename = download_file(
        url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
        checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f'
    )

    with pytest.raises(ValidationError) as exception_info:
        read_model_description(filename, validate=True, validate_variable_names=True)

    assert len(exception_info.value.problems) == 124

@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_validate_start_values():

    filename = download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

    with pytest.raises(Exception) as exception_info:
        simulate_fmu(filename, start_values={'clutch1.sa': 0.0})

    assert 'The start values for the following variables could not be set: clutch1.sa' == str(exception_info.value)


def test_validate_fmu_preserves_archive_problems(tmp_path):
    import zipfile
    from fmpy.validation import validate_fmu

    fmu_path = tmp_path / "test_archive_problems.fmu"
    invalid_xml = "<fmiModelDescription><invalid></fmiModelDescription>"

    with zipfile.ZipFile(fmu_path, "w") as zf:
        zf.writestr("resources\\file.txt", "dummy content")
        zf.writestr("modelDescription.xml", invalid_xml)

    problems = validate_fmu(str(fmu_path))
    assert any('The file path "resources\\file.txt" contains a backslash.' in p for p in problems)
    assert len(problems) >= 2
