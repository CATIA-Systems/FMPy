import unittest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy import CO_SIMULATION, MODEL_EXCHANGE

class ExamplesTest(unittest.TestCase):

    def test_coupled_clutches_example(self):

        for fmi_version in ['1.0', '2.0']:
            for fmi_type in [CO_SIMULATION, MODEL_EXCHANGE]:
                simulate_coupled_clutches(fmi_version=fmi_version, fmi_type=fmi_type, show_plot=False)

        # TODO: add assertions


if __name__ == '__main__':

    unittest.main()
