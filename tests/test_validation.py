from fmpy import read_model_description, simulate_fmu

import unittest

from fmpy.model_description import ValidationError
from fmpy.util import download_file, download_test_file


class ValidationTest(unittest.TestCase):
    """ Test the validation of model description """


    def test_validate_derivatives(self):

        filename = download_file(
            url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
            checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f'
        )

        problems = []

        try:
            read_model_description(filename, validate=True, validate_variable_names=False)
        except ValidationError as e:
            problems = e.problems

        self.assertEqual(problems[0], 'The unit "" of variable "inputs" (line 183) is not defined.')

    def test_validate_variable_names(self):

        filename = download_file(
            url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
            checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f'
        )

        problems = []

        try:
            read_model_description(filename, validate=True, validate_variable_names=True)
        except ValidationError as e:
            problems = e.problems

        self.assertEqual(len(problems), 124)

    def test_validate_start_values(self):

        filename = download_test_file('2.0', 'ModelExchange', 'MapleSim', '2016.2', 'CoupledClutches', 'CoupledClutches.fmu')

        with self.assertRaises(Exception) as context:
            simulate_fmu(filename, start_values={'clutch1.sa': 0.0})

        self.assertTrue('Variable "clutch1.sa" has inital=calculated and cannot be set.' == str(context.exception))


if __name__ == '__main__':
    unittest.main()
