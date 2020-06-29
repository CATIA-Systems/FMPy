import unittest
from fmpy import read_model_description, simulate_fmu
from fmpy.util import download_test_file
from fmpy.cswrapper import add_cswrapper


class CSWrapperTest(unittest.TestCase):

    def test_cswrapper(self):

        filename = 'CoupledClutches.fmu'

        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', filename)

        model_description = read_model_description(filename)

        self.assertIsNone(model_description.coSimulation)

        add_cswrapper(filename)

        simulate_fmu(filename, fmi_type='CoSimulation')
