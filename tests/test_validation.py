from fmpy import read_model_description

import unittest
from fmpy.util import download_file


class ValidationTest(unittest.TestCase):
    """ Test the validation of model description """

    def setUp(self):
        download_file(url='https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win64/MapleSim/2015.1/CoupledClutches/CoupledClutches.fmu',
                      checksum='af8f8ca4d7073b2d6207d8eea4a3257e3a23a69089f03181236ee3ecf13ff77f')

    def test_validate_derivatives(self):

        message = None

        try:
            read_model_description('CoupledClutches.fmu', validate=True, validate_variable_names=False)
        except Exception as e:
            message = str(e)

        self.assertEqual(message, 'The unit "" of variable "inputs" (line 183) is not defined.')

    def test_validate_variable_name(self):

        message = None

        try:
            read_model_description('CoupledClutches.fmu', validate=False, validate_variable_names=True)
        except Exception as e:
            message = str(e)

        self.assertTrue(message.startswith('"CoupledClutches_r(19)" (line 192) is not a legal variable name for naming convention "structured".'))


if __name__ == '__main__':
    unittest.main()
