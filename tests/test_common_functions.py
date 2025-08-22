import pytest

from fmpy import read_model_description, extract
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave
import shutil


@pytest.mark.parametrize('fmi_version', ['1.0', '2.0'])
def test_common_functions(fmi_version, reference_fmus_dist_dir):

    model_name = 'Feedthrough'

    if fmi_version == '1.0':
        filename = reference_fmus_dist_dir / fmi_version / 'cs' / f'{model_name}.fmu'
    else:
        filename = reference_fmus_dist_dir / fmi_version / f'{model_name}.fmu'

    model_description = read_model_description(filename)

    unzipdir = extract(filename)

    guid = model_description.guid

    variables = {}

    for v in model_description.modelVariables:
        variables[v.name] = v

    args = {
        'guid': guid,
        'modelIdentifier': model_description.coSimulation.modelIdentifier,
        'unzipDirectory': unzipdir,
        'instanceName': None
    }

    if fmi_version == '1.0':
        fmu = FMU1Slave(**args)
        fmu.instantiate("instance1")
        fmu.initialize()
    else:
        fmu = FMU2Slave(**args)
        fmu.instantiate(loggingOn=False)
        fmu.setupExperiment(tolerance=None)
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    # get types platform
    types_platform = fmu.getTypesPlatform()

    if fmi_version == '1.0':
        assert 'standard32' == types_platform
    else:
        assert 'default' == types_platform

    # get FMI version
    version = fmu.getVersion()
    assert fmi_version == version

    # set debug logging
    if fmi_version == '1.0':
        fmu.setDebugLogging(True)
    else:
        fmu.setDebugLogging(True, ['logEvents'])

    # set and get Real
    vr = [variables['Float64_continuous_input'].valueReference]
    value = [30.0]
    fmu.setReal(vr, value)
    result = fmu.getReal(vr)
    assert result[0] == value[0]

    # set and get Integer
    vr = [variables['Int32_input'].valueReference]
    value = [-4]
    fmu.setInteger(vr, value)
    result = fmu.getInteger(vr)
    assert result[0] == value[0]

    # set and get Boolean
    vr = [variables['Boolean_input'].valueReference]
    value = [True]
    fmu.setBoolean(vr, value)
    result = fmu.getBoolean(vr)
    assert result[0] == value[0]

    # set and get String
    vr = [variables['String_input'].valueReference]
    value = ['foo']
    fmu.setString(vr, value)
    result = fmu.getString(vr)
    assert result[0].decode('utf-8') == value[0]

    # clean up
    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir)
