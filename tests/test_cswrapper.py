from fmpy import read_model_description, simulate_fmu
from fmpy.util import download_test_file
from fmpy.cswrapper import add_cswrapper


def test_cswrapper():

    filename = 'CoupledClutches.fmu'

    download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', filename)

    model_description = read_model_description(filename)

    assert model_description.coSimulation is None

    outfilename = filename[:-4] + '_cs.fmu'

    add_cswrapper(filename, outfilename=outfilename)

    simulate_fmu(outfilename, fmi_type='CoSimulation')
