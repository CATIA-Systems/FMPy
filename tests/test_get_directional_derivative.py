import pytest
from shutil import rmtree
from fmpy import platform, read_model_description, extract
from fmpy.util import download_test_file
from fmpy.fmi2 import FMU2Slave


@pytest.mark.skipif(platform not in ['win32', 'win64'], reason="Current platform not supported by this FMU")
def test_get_directional_derivative():

    fmu_filename = 'Rectifier.fmu'

    download_test_file('2.0', 'CoSimulation', 'Dymola', '2017', 'Rectifier', fmu_filename)

    model_description = read_model_description(filename=fmu_filename)

    unzipdir = extract(fmu_filename)

    fmu = FMU2Slave(guid=model_description.guid,
                    unzipDirectory=unzipdir,
                    modelIdentifier=model_description.coSimulation.modelIdentifier)

    fmu.instantiate()
    fmu.setupExperiment()
    fmu.enterInitializationMode()

    # get the partial derivative for an initial unknown
    unknown = model_description.initialUnknowns[1]

    assert 'iAC[1]' == unknown.variable.name

    vrs_unknown = [unknown.variable.valueReference]
    vrs_known = [v.valueReference for v in unknown.dependencies]
    dv_known = [1.0] * len(unknown.dependencies)

    partial_der = fmu.getDirectionalDerivative(vUnknown_ref=vrs_unknown, vKnown_ref=vrs_known, dvKnown=dv_known)

    assert [-2.0] == partial_der

    fmu.exitInitializationMode()

    # get the partial derivative for three output variables
    unknowns = model_description.outputs[4:7]

    assert ['uAC[1]', 'uAC[2]', 'uAC[3]'] == [u.variable.name for u in unknowns]

    vrs_unknown = [u.variable.valueReference for u in unknowns]
    vrs_known = [v.valueReference for v in unknowns[0].dependencies]
    dv_known = [1.0] * len(vrs_known)

    partial_der = fmu.getDirectionalDerivative(vUnknown_ref=vrs_unknown, vKnown_ref=vrs_known, dvKnown=dv_known)

    assert pytest.approx(-1500) == partial_der[0]
    assert pytest.approx(0) == partial_der[1]
    assert pytest.approx(1500) == partial_der[2]

    fmu.terminate()
    fmu.freeInstance()
    rmtree(unzipdir)
