import numpy as np
from fmpy.util import write_csv, read_csv


def test_write_and_read_csv(work_dir):

    cols = [
        ('time', np.float64, None),
        ('y1', np.float64, None),
        ('y2', np.float64, (3,)),
    ]

    rows = [
        (0.0, 0, (1.0, 2.0, 3.0)),
        (0.1, 1, (1.1, 2.1, 3.1)),
        (0.2, 2, (1.2, 2.2, 3.2)),
        (0.3, 3, (1.3, 2.3, 3.3)),
    ]

    expected = np.array(rows, dtype=np.dtype(cols))

    filename = work_dir / 'arrays.csv'

    write_csv(filename, expected)

    result = read_csv(filename)

    assert np.all(result == expected)
