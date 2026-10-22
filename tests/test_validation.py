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


def test_validate_fmi3_initial_unknowns_clocks_and_clocked(tmp_path):
    """
    Test FMI 3.0 ModelStructure/InitialUnknowns validation (#910):
    - Output Clocks are not expected in InitialUnknowns.
    - Listing an unclocked Clock in InitialUnknowns is rejected.
    - Clocked output variables are allowed (optional) in InitialUnknowns.
    """
    def create_model_description(initial_unknowns_vrs, extra_variables="", output_vrs=(2, 3)):
        outputs_xml = "".join(f'<Output valueReference="{vr}"/>' for vr in output_vrs)
        unknowns_xml = "".join(f'<InitialUnknown valueReference="{vr}"/>' for vr in initial_unknowns_vrs)
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<fmiModelDescription fmiVersion="3.0" modelName="ClockTest" instantiationToken="{{00000000-0000-0000-0000-000000000000}}">
  <CoSimulation modelIdentifier="ClockTest" hasEventMode="true"/>
  <ModelVariables>
    <Float64 name="time" valueReference="0" causality="independent" variability="continuous"/>
    <Clock name="inClock" valueReference="1" causality="input" intervalVariability="triggered"/>
    <Clock name="alarm" valueReference="2" causality="output" intervalVariability="triggered"/>
    <Float64 name="y" valueReference="3" causality="output" variability="discrete"/>
    {extra_variables}
  </ModelVariables>
  <ModelStructure>
    {outputs_xml}
    {unknowns_xml}
  </ModelStructure>
</fmiModelDescription>
"""
        file_path = tmp_path / "modelDescription.xml"
        file_path.write_text(xml, encoding="utf-8")
        return str(file_path)

    # Case 1: InitialUnknowns = {y} (vr 3) -> valid (alarm is an output Clock, not expected in InitialUnknowns)
    md_file = create_model_description([3])
    md = read_model_description(md_file, validate=True, validate_model_structure=True)
    assert md.modelName == "ClockTest"

    # Case 2: InitialUnknowns = {alarm, y} (vrs 2, 3) -> invalid (alarm is a Clock without clocks attribute, rejected)
    md_file = create_model_description([2, 3])
    with pytest.raises(ValidationError) as ex:
        read_model_description(md_file, validate=True, validate_model_structure=True)
    assert any("ModelStructure/InitialUnknowns does not contain the expected set of variables" in p for p in ex.value.problems)

    # Case 3a: InitialUnknowns = {y, z} where z is clocked output -> valid (clocked output in InitialUnknowns)
    extra_var = '<Int32 name="z" valueReference="4" causality="output" variability="discrete" clocks="1"/>'
    md_file = create_model_description([3, 4], extra_variables=extra_var, output_vrs=(2, 3, 4))
    md = read_model_description(md_file, validate=True, validate_model_structure=True)
    assert md.modelName == "ClockTest"

    # Case 3b: InitialUnknowns = {y} where z is clocked output -> valid (clocked output omitted from InitialUnknowns)
    md_file = create_model_description([3], extra_variables=extra_var, output_vrs=(2, 3, 4))
    md = read_model_description(md_file, validate=True, validate_model_structure=True)
    assert md.modelName == "ClockTest"

    # Case 4: InitialUnknowns is missing required unclocked output y -> invalid
    md_file = create_model_description([])
    with pytest.raises(ValidationError) as ex:
        read_model_description(md_file, validate=True, validate_model_structure=True)
    assert any("ModelStructure/InitialUnknowns does not contain the expected set of variables" in p for p in ex.value.problems)
