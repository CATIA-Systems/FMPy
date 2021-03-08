import unittest
from fmpy.util import download_file, validate_result
from fmpy import *

v = '0.0.5'  # Reference FMUs version


class ReferenceFMUsTest(unittest.TestCase):

    def setUp(self):
        download_file(url='https://github.com/modelica/Reference-FMUs/releases/download/v' + v + '/Reference-FMUs-' + v + '.zip',
                      checksum='07291b9223ac2b479078afd4acea42d13118a64c2c1b5aa7a3c6f987585358fd')
        extract('Reference-FMUs-' + v + '.zip', 'Reference-FMUs-dist')

        download_file(url='https://github.com/modelica/Reference-FMUs/archive/v' + v + '.zip',
                      checksum='2c2f10626bc8c6104e42e4565a2b0a3cb72829c6059dcbe8dc1dc102a5a1689d')
        extract('v' + v + '.zip', 'Reference-FMUs-repo')

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

                in_csv = os.path.join('Reference-FMUs-repo', 'Reference-FMUs-' + v, model_name, model_name + '_in.csv')
                input = read_csv(in_csv) if os.path.isfile(in_csv) else None
            else:
                start_values = {}
                input = None

            filename = os.path.join('Reference-FMUs-dist', '3.0', model_name + '.fmu')

            ref_csv = os.path.join('Reference-FMUs-repo', 'Reference-FMUs-' + v, model_name, model_name + '_ref.csv')
            reference = read_csv(ref_csv)

            for fmi_type in ['ModelExchange', 'CoSimulation']:
                result = simulate_fmu(filename, fmi_type=fmi_type, start_values=start_values, input=input)
                rel_out = validate_result(result, reference)
                self.assertEqual(0, rel_out)
                # plot_result(result, reference)

    @unittest.skip("XML of Clock.fmu is broken")
    def test_fmi3_clocks(self):
        """ Test the SE specific API """

        import shutil
        from fmpy.fmi3 import FMU3ScheduledExecution

        filename = os.path.join(os.getcwd(), 'Reference-FMUs-dist', '3.0', 'Clocks.fmu')

        model_description = read_model_description(filename)

        unzipdir = extract(filename)

        fmu = instantiate_fmu(unzipdir, model_description, fmi_type='ScheduledExecution')

        fmu.instantiate()

        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        fmu.activateModelPartition(clockReference=1001, clockElementIndex=0, activationTime=0)

        fmu.terminate()
        fmu.freeInstance()

        shutil.rmtree(unzipdir, ignore_errors=True)
