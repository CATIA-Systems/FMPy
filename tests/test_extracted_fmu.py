import shutil
from fmpy import extract, read_model_description, simulate_fmu
from fmpy.util import download_test_file


def test_extracted_fmu():
    """ Simulate an extracted FMU """

    download_test_file('2.0', 'cs', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

    # extract the FMU
    tempdir = extract('CoupledClutches.fmu')

    # load the model description before the simulation
    model_description = read_model_description(tempdir)

    result = simulate_fmu(tempdir, model_description=model_description)

    assert result is not None

    # clean up
    shutil.rmtree(tempdir)
