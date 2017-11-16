import unittest
from unittest import skipIf
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy.examples.custom_input import simulate_custom_input
from fmpy.examples.parameter_variation import run_experiment
from fmpy.ssp.examples.controlled_drivetrain import simulate_controlled_drivetrain
from fmpy import platform
import numpy as np
import sys


class ExamplesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Python:")
        print(sys.version)

    def test_coupled_clutches_example(self):

        if platform.startswith('win'):
            fmi_versions = ['1.0', '2.0']
        elif platform.startswith(('darwin', 'linux')):
            fmi_versions = ['2.0']
        else:
            self.fail('Platform not supported')

        for fmi_version in fmi_versions:
            for fmi_type in ['CoSimulation', 'ModelExchange']:

                solvers = ['Euler']

                if fmi_type == 'ModelExchange':
                    solvers.append('CVode')

                for solver in solvers:

                    result = simulate_coupled_clutches(fmi_version=fmi_version,
                                                       fmi_type=fmi_type,
                                                       solver=solver,
                                                       show_plot=False,
                                                       output=['inputs', 'CoupledClutches1_freqHz'])

                    if result is not None:  # sometimes the download fails...

                        # check if the start value has been set
                        freqHz = result['CoupledClutches1_freqHz']
                        self.assertTrue(np.all(freqHz == 0.4))

                        # check if the input has been set
                        inputs = result['inputs']
                        self.assertAlmostEqual(inputs[0], 0)
                        self.assertAlmostEqual(inputs[-1], 1)

    def test_custom_input_example(self):
        end_time = simulate_custom_input(show_plot=False)
        self.assertAlmostEqual(end_time, 1.1)

    @skipIf(platform not in ['win32', 'win64'], "FMU only available for Windows")
    def test_parameter_variation(self):
        LOSSES = run_experiment(show_plot=False)
        self.assertTrue(np.all(LOSSES > 0))

    @skipIf(platform not in ['win32', 'win64'], "SSP only available for Windows")
    def test_controlled_drivetrain_example(self):
        result = simulate_controlled_drivetrain(show_plot=False)
        self.assertAlmostEqual(result['time'][-1], 4)
        self.assertTrue(result['controller.y'][-1] > -11)
        self.assertTrue(result['controller.y'][-1] < -9)


if __name__ == '__main__':
    unittest.main()
