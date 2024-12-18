import pytest
from subprocess import check_call
from fmpy.util import download_test_file, create_jupyter_notebook


@pytest.mark.skipif(True, reason="Fails in GitHub Actions")
def test_create_juypter_notebook():

    download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

    create_jupyter_notebook('CoupledClutches.fmu')

    args = ['jupyter', 'nbconvert', '--to', 'notebook', '--execute',
            '--ExecutePreprocessor.timeout=60',
            '--output', 'CoupledClutches_out.ipynb', 'CoupledClutches.ipynb']

    check_call(args)
