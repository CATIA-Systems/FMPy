import unittest
from fmpy import platform, dump
from fmpy.util import download_test_file, fmu_info


class FMUInfoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # download the FMU
        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2017', 'CoupledClutches', 'CoupledClutches.fmu')

    def test_fmu_info(self):

        info = fmu_info('CoupledClutches.fmu')

        generation_dates = {
            'darwin64': '2017-10-04T12:04:24Z',
            'linux64':  '2017-10-04T12:03:05Z',
            'win32':    '2017-10-04T12:08:16Z',
            'win64':    '2017-10-04T12:06:59Z',
        }

        expected = """
Model Info

  FMI Version       2.0
  Model Name        CoupledClutches
  Description       Model CoupledClutches
  Platforms         %s
  Continuous States 18
  Event Indicators  25
  Variables         178
  Generation Tool   MapleSim (1267140/1267140/1267140)
  Generation Date   %s

Default Experiment

  Stop Time         1.5
  Tolerance         0.0001

Variables (input, output)

Name                Causality      Start  Unit     Description
inputs              input            0.0           RI1
outputs[1]          output          10.0  rad/s    J1.w
outputs[2]          output           0.0  rad/s    J2.w
outputs[3]          output           0.0  rad/s    J3.w
outputs[4]          output           0.0  rad/s    J4.w""" % (platform, generation_dates[platform])

        self.assertEqual(expected, info)

    def test_dump(self):
        # dump the FMU info
        dump('CoupledClutches.fmu')
