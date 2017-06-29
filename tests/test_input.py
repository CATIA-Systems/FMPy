import unittest
import numpy as np

from fmpy.simulation import Input


class InputTest(unittest.TestCase):

    def test_input_continuous(self):

        t = np.array([0, 1, 2, 3])
        y = np.array([[0, 0, 3, 3], [-1, 0, 1, 2]])

        # extrapolate left
        v1, v2 = Input.interpolate(-1, t, y)
        self.assertEqual(v1, 0)
        self.assertEqual(v2, -2)

        # hit sample
        v1, v2 = Input.interpolate(1, t, y)
        self.assertEqual(v1, 0)
        self.assertEqual(v2, 0)

        # interpolate
        v1, v2 = Input.interpolate(1.5, t, y)
        self.assertEqual(v1, 1.5)
        self.assertEqual(v2, 0.5)

        # extrapolate right
        v1, v2 = Input.interpolate(4, t, y)
        self.assertEqual(v1, 3)
        self.assertEqual(v2, 3)

    def test_input_discrete(self):

        t = np.array([0, 1, 1, 2])
        y = np.array([[0, 0, 3, 3]])

        # extrapolate left
        v = Input.interpolate(-1, t, y)
        self.assertEqual(v, 0)

        # hit sample
        v = Input.interpolate(0, t, y)
        self.assertEqual(v, 0)

        # interpolate
        v = Input.interpolate(0.5, t, y)
        self.assertEqual(v, 0)

        # before event
        v = Input.interpolate(1, t, y)
        self.assertEqual(v, 0)

        # after event
        v = Input.interpolate(1, t, y, after_event=True)
        self.assertEqual(v, 3)

        # extrapolate right
        v = Input.interpolate(0, t, y)
        self.assertEqual(v, 0)


if __name__ == '__main__':

    unittest.main()
