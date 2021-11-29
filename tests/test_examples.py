import unittest
from unittest import skipIf
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy.examples.custom_input import simulate_custom_input
from fmpy.examples.efficient_loops import run_efficient_loop
from fmpy.examples.parameter_variation import run_experiment
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
            fmi_versions = ['2.0']  # ['1.0', '2.0'] quick fix until 1.0 is available again
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

                        freqHz = result['CoupledClutches1_freqHz']
                        self.assertTrue(np.all(freqHz == 0.4), "Start value has not been applied")

                        inputs = result['inputs']
                        self.assertAlmostEqual(inputs[0], 0, "Input has not been applied")
                        self.assertAlmostEqual(inputs[-1], 1, "Input has not been applied")

                        self.assertEqual(0.0, result['time'][0], msg="Result must start at start_time (= 0.0)")

    def test_custom_input_example(self):
        end_time = simulate_custom_input(show_plot=False)
        self.assertAlmostEqual(end_time, 1.1, delta=1e-2)

    def test_efficient_loops(self):
        run_efficient_loop()

    @skipIf(platform not in ['win32', 'win64'], "FMU only available for Windows")
    def test_parameter_variation(self):
        LOSSES = run_experiment(show_plot=False)
        self.assertTrue(np.all(LOSSES > 0))


if __name__ == '__main__':
    unittest.main()
