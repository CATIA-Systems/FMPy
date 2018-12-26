import unittest
import numpy as np
import sys

from fmpy.simulation import Input


class InputTest(unittest.TestCase):

    def test_input_continuous(self):

        t = np.array( [ 0, 1, 2, 3])
        y = np.array([[ 0, 0, 3, 3],
                      [-1, 0, 1, 2]])

        # extrapolate left (hold)
        v1, v2 = Input.interpolate(-1, t, y)
        self.assertEqual(v1,  0)
        self.assertEqual(v2, -1)

        # hit sample
        v1, v2 = Input.interpolate(1, t, y)
        self.assertEqual(v1, 0)
        self.assertEqual(v2, 0)

        # interpolate (linear)
        v1, v2 = Input.interpolate(1.5, t, y)
        self.assertAlmostEqual(v1, 1.5)
        self.assertAlmostEqual(v2, 0.5)

        # extrapolate right (hold)
        v1, v2 = Input.interpolate(4, t, y)
        self.assertEqual(v1, 3)
        self.assertEqual(v2, 2)

    def test_event_detection(self):

        fmx = sys.float_info.max

        dtype = np.dtype([('time', np.float64)])

        # no event
        signals = np.array([(0,), (1,)], dtype=dtype)
        t_events = Input.findEvents(signals)
        self.assertEqual([fmx], t_events)

        # time grid with events at 0.5 and 0.8
        signals = np.array(list(zip([0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.8, 0.8, 0.9, 1.0])), dtype=dtype)
        t_events = Input.findEvents(signals)
        self.assertTrue(np.all([0.5, 0.8, fmx] == t_events))

    def test_input_discrete(self):

        t = np.array( [0, 1, 1, 1, 2])
        y = np.array([[0, 0, 4, 3, 3]])

        # extrapolate left
        v = Input.interpolate(-1, t, y)
        self.assertEqual(v, 0, "Expecting first value")

        # hit sample
        v = Input.interpolate(0, t, y)
        self.assertEqual(v, 0, "Expecting value at sample")

        # interpolate
        v = Input.interpolate(0.5, t, y)
        self.assertEqual(v, 0, "Expecting to hold previous value")

        # before event
        v = Input.interpolate(1, t, y)
        self.assertEqual(v, 0, "Expecting value before event")

        # after event
        v = Input.interpolate(1, t, y, after_event=True)
        self.assertEqual(v, 3, "Expecting value after event")

        # extrapolate right
        v = Input.interpolate(3, t, y)
        self.assertEqual(v, 3, "Expecting last value")


if __name__ == '__main__':

    unittest.main()
