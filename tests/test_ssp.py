import unittest
from unittest import skipIf
import numpy as np
import sys
from fmpy import platform
from fmpy.ssp.ssd import read_ssd, read_ssv
from fmpy.ssp.simulation import simulate_ssp
import os


@skipIf('SSP_EXAMPLES_DIR' not in os.environ, "Environment variable SSP_EXAMPLES_DIR is required for this test")
class SSPTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Python:", sys.version)
        print()

    @staticmethod
    def ssp_example_path(filename):
        return os.path.join(os.environ['SSP_EXAMPLES_DIR'], filename)

    @skipIf(platform != 'win32', "Current platform not supported by this SSP")
    def test_simulate_sample_system_with_parameters(self):

        ssv_filename = self.ssp_example_path('SampleSystemParameterValues.ssv')
        parameters = read_ssv(ssv_filename)

        filename = self.ssp_example_path('SampleSystem.ssp')
        sine = lambda t: np.sin(t * 2 * np.pi)
        result = simulate_ssp(filename, stop_time=1.0, step_size=0.01, parameters=parameters, input={'In1': sine})

        # check if the input has been applied correctly
        self.assertTrue(np.all(np.abs(result['In1'] - sine(result['time'])) < 0.01))

        # plot_result(result, names=['In1', 'Out1'], window_title=filename)

    @skipIf(platform != 'win32', "Current platform not supported by this SSP")
    def test_simulate_sub_system(self):

        ssp_filename = self.ssp_example_path('SampleSystemSubSystem.ssp')
        sine = lambda t: np.sin(t * 2 * np.pi)
        result = simulate_ssp(ssp_filename, stop_time=1.0, step_size=0.01, input={'In1': sine})

        # check if the input has been applied correctly
        self.assertTrue(np.all(np.abs(result['In1'] - sine(result['time'])) < 0.01))

        # plot_result(result, names=['In1', 'Out1'], window_title=ssp_filename)

    def test_read_ssd_dictionary(self):
        filename = self.ssp_example_path('SampleSystemSubSystemDictionary.ssp')
        ssd = read_ssd(filename)
        self.assertEqual(ssd.name, 'Simple System with SubSystem and Dictionary')

    # def test_ControlledTemperature(self):
    #
    #     ssp_filename = r'ControlledTemperature.ssp'
    #
    #     if not os.path.isfile(ssp_filename):
    #         return
    #
    #     def Tenv(t):
    #         return 20.0
    #
    #     def Tref(t):
    #         return 20.0 + np.floor(t) * 3
    #
    #     result = simulate_ssp(ssp_filename, stop_time=10, step_size=1e-2, input={'Tenv': Tenv, 'Tref': Tref})
    #
    #     # plot_result(result, names=['Tenv', 'Tref', 'controller.onSwitch', 'T'], window_title=os.path.basename(ssp_filename))

    # def test_eDrive(self):
    #     ssp_filename = r'Z:\Development\SSP\trunk\Examples\Electrical_Drive\Example_eDrive.ssp'
    #     # ssd = read_ssd(filename)
    #     result = simulate_ssp(ssp_filename, stop_time=1.0)
    #     # self.assertEqual(ssd.name, 'ElectricalDrive')


if __name__ == '__main__':
    unittest.main()
