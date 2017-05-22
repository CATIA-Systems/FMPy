import unittest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches


class TestFMUInfo(unittest.TestCase):

    def test_coupled_clutches_example(self):

        simulate_coupled_clutches(False)


if __name__ == '__main__':

    unittest.main()
