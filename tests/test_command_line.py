import unittest
from subprocess import call, check_output
from fmpy.util import download_test_file, download_file


class CommandLineTest(unittest.TestCase):
    """ Test command line interface ('fmpy' entry point must be registered through setup.py or conda package) """

    @classmethod
    def setUpClass(cls):
        # download the FMU and input file
        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')
        download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches_in.csv')
        download_file('https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/Dymola/2019FD01/Rectifier/Rectifier.fmu')

    def test_info(self):
        status = call(['fmpy', 'info', 'CoupledClutches.fmu'])
        self.assertEqual(0, status)

    def test_validate(self):
        status = call(['fmpy', 'validate', 'Rectifier.fmu'])
        self.assertEqual(0, status)

    def test_simulate(self):

        output = check_output([
            'fmpy', 'simulate', 'CoupledClutches.fmu',
            '--validate',
            '--start-time', '0',
            '--stop-time', '0.1',
            '--solver', 'CVode',
            '--relative-tolerance', '1e-4',
            '--dont-record-events',
            '--start-values', 'CoupledClutches1_freqHz', '0.2',
            '--apply-default-start-values',
            '--output-interval', '1e-2',
            '--input-file', 'CoupledClutches_in.csv',
            '--output-variables', 'outputs[1]', 'outputs[3]',
            '--output-file', 'CoupledClutches_out.csv',
            '--timeout', '10',
            '--debug-logging',
            '--fmi-logging',
            # '--show-plot',
        ])

        self.assertTrue(output.startswith(b'[OK] [ModelExchange]: GUID = {'),
                        "Placeholders have not been substituted w/ variadic arguments.")


if __name__ == '__main__':
    unittest.main()
