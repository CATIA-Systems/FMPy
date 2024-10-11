import pytest
import shutil
from fmpy import *


@pytest.mark.parametrize('fmi_version', ['2.0', '3.0'])
def test_get_output_derivatives(reference_fmus_dist_dir, fmi_version):

    filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    unzipdir = extract(filename)
    model_description = read_model_description(unzipdir)

    vr = dict((v.name, v.valueReference) for v in model_description.modelVariables)

    fmu_instance = instantiate_fmu(unzipdir=unzipdir, model_description=model_description)

    fmu_instance.enterInitializationMode()
    fmu_instance.exitInitializationMode()

    if fmi_version == '2.0':
        output_derivatives = fmu_instance.getRealOutputDerivatives(vr=[vr['h'], vr['v']], order=[1, 1])
    else:
        output_derivatives = fmu_instance.getOutputDerivatives(vr=[vr['h'], vr['v']], order=[1, 1])

    shutil.rmtree(unzipdir, ignore_errors=True)

    assert output_derivatives == [0.0, -9.81]
