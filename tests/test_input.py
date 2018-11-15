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

        # no event
        t = np.array([0.0, 1.0])
        self.assertEqual(fmx, Input.nextEvent(0.8, t), "Expecting no events")

        # time grid with events at 0.5 and 0.8
        t = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.5, 0.6, 0.7, 0.8, 0.8, 0.8, 0.9, 1.0])

        self.assertEqual(0.5, Input.nextEvent(0.0, t), "Expecting first event before first sample")
        self.assertEqual(0.5, Input.nextEvent(0.2, t), "Expecting first event before first event")
        self.assertEqual(0.8, Input.nextEvent(0.5, t), "Expecting second event at first event")
        self.assertEqual(0.8, Input.nextEvent(0.6, t), "Expecting second event between first and second event")
        self.assertEqual(fmx, Input.nextEvent(0.8, t), "Expecting no more events after second (multi) event")
        self.assertEqual(fmx, Input.nextEvent(1.0, t), "Expecting no more events after last event")
        self.assertEqual(fmx, Input.nextEvent(2.0, t), "Expecting no more events after last sample")

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
