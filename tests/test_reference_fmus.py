import unittest
from fmpy.util import download_file, validate_result
from fmpy import *


class ReferenceFMUsTest(unittest.TestCase):

    def setUp(self):
        download_file(url='https://github.com/modelica/Reference-FMUs/releases/download/v0.0.3/Reference-FMUs-0.0.3.zip',
                      checksum='f9b5c0199127d174e38583fc8733de4286dfd1da8236507007ab7b38f0e32796')
        extract('Reference-FMUs-0.0.3.zip', 'Reference-FMUs-dist')

        download_file(url='https://github.com/modelica/Reference-FMUs/archive/v0.0.3.zip',
                      checksum='ce58f006d3fcee52261ce2f7a3dad635161d4dcaaf0e093fdcd5ded7ee0df647')
        extract('v0.0.3.zip', 'Reference-FMUs-repo')

    def test_fmi1_cs(self):
        for model_name in ['BouncingBall', 'Dahlquist', 'Resource', 'Stair', 'VanDerPol']:
            filename = os.path.join('Reference-FMUs-dist', '1.0', 'cs', model_name + '.fmu')
            result = simulate_fmu(filename)
            # plot_result(result)

    def test_fmi1_me(self):
        for model_name in ['BouncingBall', 'Dahlquist', 'Stair', 'VanDerPol']:
            filename = os.path.join('Reference-FMUs-dist', '1.0', 'me', model_name + '.fmu')
            result = simulate_fmu(filename)
            # plot_result(result)

    def test_fmi2(self):
        for model_name in ['BouncingBall', 'Dahlquist', 'Feedthrough', 'Resource', 'Stair', 'VanDerPol']:
            filename = os.path.join('Reference-FMUs-dist', '2.0', model_name + '.fmu')
            for fmi_type in ['ModelExchange', 'CoSimulation']:
                result = simulate_fmu(filename, fmi_type=fmi_type)
                # plot_result(result)

    def test_fmi3(self):

        for model_name in ['BouncingBall', 'Dahlquist', 'Feedthrough', 'Resource', 'Stair', 'VanDerPol']:

            if model_name == 'Feedthrough':
                start_values = {
                    'real_fixed_param': 1,
                    'string_param':     "FMI is awesome!"
                }

                in_csv = os.path.join('Reference-FMUs-repo', 'Reference-FMUs-0.0.3', model_name, model_name + '_in.csv')
                input = read_csv(in_csv) if os.path.isfile(in_csv) else None
            else:
                start_values = {}
                input = None

            filename = os.path.join('Reference-FMUs-dist', '3.0', model_name + '.fmu')

            ref_csv = os.path.join('Reference-FMUs-repo', 'Reference-FMUs-0.0.3', model_name, model_name + '_ref.csv')
            reference = read_csv(ref_csv)

            for fmi_type in ['ModelExchange', 'CoSimulation']:
                result = simulate_fmu(filename, fmi_type=fmi_type, start_values=start_values, input=input)
                rel_out = validate_result(result, reference)
                self.assertEqual(0, rel_out)
                # plot_result(result, reference)
