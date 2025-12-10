import pytest
from fmpy import read_model_description, simulate_fmu, platform_tuple
from fmpy.util import download_test_file
from fmpy.cswrapper import add_cswrapper


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_cswrapper():

    filename = 'CoupledClutches.fmu'

    download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', filename)

    model_description = read_model_description(filename)

    assert model_description.coSimulation is None

    outfilename = filename[:-4] + '_cs.fmu'

    add_cswrapper(filename, outfilename=outfilename)

    simulate_fmu(outfilename, fmi_type='CoSimulation')
