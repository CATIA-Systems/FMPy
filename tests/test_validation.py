from fmpy import read_model_description

import unittest

from fmpy.model_description import ValidationError
from fmpy.util import download_file


class ValidationTest(unittest.TestCase):
    """ Test the validation of model description """

    def setUp(self):
        download_file(url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
                      checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f')

    def test_validate_derivatives(self):

        problems = []

        try:
            read_model_description('CoupledClutches.fmu', validate=True, validate_variable_names=False)
        except ValidationError as e:
            problems = e.problems

        self.assertEqual(problems[0], 'The unit "" of variable "inputs" (line 183) is not defined.')

    def test_validate_variable_names(self):

        problems = []

        try:
            read_model_description('CoupledClutches.fmu', validate=True, validate_variable_names=True)
        except ValidationError as e:
            problems = e.problems

        self.assertEqual(len(problems), 124)


if __name__ == '__main__':
    unittest.main()
