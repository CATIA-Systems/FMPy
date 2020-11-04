import sys
import unittest
from subprocess import check_call
from fmpy.util import download_test_file, create_jupyter_notebook


@unittest.skipIf(sys.version_info[0] < 3, "Python 2.7 supported on CI")
class JupyterNotebookTest(unittest.TestCase):
    """ Test the Jupyter Notebook generation """

    def test_create_juypter_notebook(self):

        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

        create_jupyter_notebook('CoupledClutches.fmu')

        args = ['jupyter', 'nbconvert', '--to', 'notebook', '--execute',
                '--ExecutePreprocessor.timeout=60',
                '--output', 'CoupledClutches_out.ipynb', 'CoupledClutches.ipynb']

        check_call(args)


if __name__ == '__main__':
    unittest.main()
