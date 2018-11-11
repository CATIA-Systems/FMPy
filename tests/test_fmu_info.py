import unittest
from fmpy import platform, dump, simulate_fmu
from fmpy.util import download_test_file, fmu_info


class FMUInfoTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # download the FMU
        download_test_file('2.0', 'me', 'MapleSim', '2018', 'CoupledClutches', 'CoupledClutches.fmu')

    def test_illegal_fmi_type(self):
        with self.assertRaises(Exception) as context:
            simulate_fmu('CoupledClutches.fmu', fmi_type='Hybrid')
        self.assertEqual('fmi_type must be one of "ModelExchange" or "CoSimulation"', str(context.exception))

    def test_unsupported_fmi_type(self):
        with self.assertRaises(Exception) as context:
            simulate_fmu('CoupledClutches.fmu', fmi_type='CoSimulation')
        self.assertEqual('FMI type "CoSimulation" is not supported by the FMU', str(context.exception))

    def test_fmu_info(self):

        info = fmu_info('CoupledClutches.fmu')

        generation_dates = {
            'darwin64': '2018-10-25T13:27:34Z',
            'linux64':  '2018-10-25T13:26:02Z',
            'win32':    '2018-10-25T13:24:25Z',
            'win64':    '2018-10-25T13:27:23Z',
        }

        expected = """
Model Info

  FMI Version       2.0
  FMI Type          Model Exchange
  Model Name        CoupledClutches
  Description       Model CoupledClutches
  Platforms         %s
  Continuous States 18
  Event Indicators  25
  Variables         178
  Generation Tool   MapleSim (1357016/1357197/1357197)
  Generation Date   %s

Default Experiment

  Stop Time         1.5
  Tolerance         0.0001

Variables (input, output)

Name                Causality              Start Value  Unit     Description
inputs              input      0.00000000000000000e+00           RI1
outputs[1]          output     1.00000000000000000e+01  rad/s    J1.w
outputs[2]          output     0.00000000000000000e+00  rad/s    J2.w
outputs[3]          output     0.00000000000000000e+00  rad/s    J3.w
outputs[4]          output     0.00000000000000000e+00  rad/s    J4.w""" % (platform, generation_dates[platform])

        self.assertEqual(expected, info)

    def test_dump(self):
        # dump the FMU info
        dump('CoupledClutches.fmu')
