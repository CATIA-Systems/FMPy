import unittest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches


class ExamplesTest(unittest.TestCase):

    def test_coupled_clutches_example(self):

        simulate_coupled_clutches(show_plot=False)

        # TODO: add assertions


if __name__ == '__main__':

    unittest.main()
