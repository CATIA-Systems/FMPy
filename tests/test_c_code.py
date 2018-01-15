from fmpy import simulate_fmu

import unittest
from fmpy.util import download_file
import os


class CCodeTest(unittest.TestCase):
    """ Test compilation of source code FMUs from various vendors """

    url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/'

    def test_compile(self):

        fmus = ['c-code/dSPACE_TargetLink/Release_2016-B/poscontrol/FmuController.fmu',
                'c-code/MapleSim/2016.2/Rectifier/Rectifier.fmu',
                'c-code/Dymola/2017/IntegerNetwork1/IntegerNetwork1.fmu']

        for fmu in fmus:
            download_file(self.url + fmu)
            filename = os.path.basename(fmu)
            result = simulate_fmu(filename=filename, use_source_code=True)
            self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
