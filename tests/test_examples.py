import unittest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy import platform
import numpy as np
import sys


class ExamplesTest(unittest.TestCase):

    def test_coupled_clutches_example(self):

        print("Python:")
        print(sys.version)

        if platform.startswith('win'):
            fmi_versions = ['1.0', '2.0']
        elif platform.startswith(('darwin', 'linux')):
            fmi_versions = ['2.0']
        else:
            self.fail('Platform not supported')

        for fmi_version in fmi_versions:
            for fmi_type in ['CoSimulation', 'ModelExchange']:

                result = simulate_coupled_clutches(fmi_version=fmi_version, fmi_type=fmi_type, show_plot=False,
                                                   output=['inputs', 'CoupledClutches1_freqHz'])

                if result is not None:  # sometimes the download fails...

                    # check if the start value has been set
                    freqHz = result['CoupledClutches1_freqHz']
                    self.assertTrue(np.all(freqHz == 0.4))

                    # check if the input has been set
                    inputs = result['inputs']
                    self.assertAlmostEqual(inputs[0], 0)
                    self.assertAlmostEqual(inputs[-1], 1)


if __name__ == '__main__':
    unittest.main()
