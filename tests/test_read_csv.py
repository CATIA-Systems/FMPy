import unittest
import numpy as np
from fmpy.util import write_csv, read_csv


class CSVTest(unittest.TestCase):

    def test_structured_csv(self):

        cols = [
            ('time', np.float64, None),
            ('y', np.float64, (3,)),
        ]

        rows = [
            (0.0, (1.0, 2.0, 3.0)),
            (0.1, (1.1, 2.1, 3.1)),
            (0.2, (1.2, 2.2, 3.2)),
            (0.3, (1.3, 2.3, 3.3)),
        ]

        # create a structured array with a 1-d array signal
        result = np.array(rows, dtype=np.dtype(cols))

        # arrays are saved as single columns
        write_csv('structured.csv', result)

        # read as-is (single columns)
        traj = read_csv('structured.csv')

        self.assertEqual(traj.dtype.names, ('time', 'y[1]', 'y[2]', 'y[3]'))

        # read structured (restore arrays)
        traj = read_csv('structured.csv', structured=True)

        self.assertEqual(traj.dtype.names, ('time', 'y'))
        self.assertEqual(traj['y'].shape, (4, 3))


if __name__ == '__main__':

    unittest.main()
