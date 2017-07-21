import unittest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy import CO_SIMULATION, MODEL_EXCHANGE, platform


class ExamplesTest(unittest.TestCase):

    def test_coupled_clutches_example(self):

        if platform.startswith('win'):
            fmi_versions = ['1.0', '2.0']
        elif platform.startswith(('darwin', 'linux')):
            fmi_versions = ['2.0']
        else:
            self.fail('Platform not supported')

        for fmi_version in fmi_versions:
            for fmi_type in [CO_SIMULATION, MODEL_EXCHANGE]:
                
                result = simulate_coupled_clutches(fmi_version=fmi_version, fmi_type=fmi_type, show_plot=False)

                if result is not None:  # sometimes the download fails
                    inputs = result['inputs']
                    self.assertAlmostEqual(inputs[0], 0.0)
                    self.assertAlmostEqual(inputs[-1], 1.0)


if __name__ == '__main__':

    unittest.main()
