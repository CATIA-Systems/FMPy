import unittest
from unittest import skipIf
import numpy as np
import fmpy
import os


@skipIf('REFERENCE_FMUS_DIR' not in os.environ, "Environment variable REFERENCE_FMUS_DIR is required for this test")
class ReferenceFMUsTest(unittest.TestCase):

    def fmu_path(self, filename):
        return os.path.join(os.environ['REFERENCE_FMUS_DIR'], filename)

    def test_bBRef(self):
        filename = self.fmu_path('fmu_bBRef.fmu')
        result = fmpy.simulate_fmu(filename, output=['h'])
        self.assertTrue(np.all(result['h'] <= 1.0))

    def test_boolRef(self):
        filename = self.fmu_path('fmu_boolRef.fmu')
        result = fmpy.simulate_fmu(filename, start_values={'a': True})
        self.assertTrue(np.all(result['c'] != 0.0))

    def test_csvRef(self):
        filename = self.fmu_path('fmu_csvRef.fmu')
        result = fmpy.simulate_fmu(filename, output=['b_'])
        self.assertTrue(np.all(result['b_'] == 9))

    def test_DLLRef_64(self):
        filename = self.fmu_path('fmu_DLLRef_64.fmu')
        result = fmpy.simulate_fmu(filename, start_values={'a_': 2.0}, output=['b_'])
        self.assertTrue(np.all(result['b_'] == 4.0))

    def test_dqRef(self):
        filename = self.fmu_path('fmu_dqRef.fmu')
        result = fmpy.simulate_fmu(filename, output=['x'])
        self.assertTrue(np.all(result['x'] <= 1.0))

    def test_dqRef(self):
        filename = self.fmu_path('fmu_dqRef.fmu')
        result = fmpy.simulate_fmu(filename, output=['x'])
        self.assertTrue(np.all(result['x'] <= 1.0))

    def test_integerRef(self):
        filename = self.fmu_path('fmu_integerRef.fmu')
        result = fmpy.simulate_fmu(filename, start_values={'a': 2, 'b': 3}, output=['c'])
        self.assertTrue(np.all(result['c'] == 5))

    def test_stringParamRef(self):
        filename = self.fmu_path('fmu_stringParamRef.fmu')
        result = fmpy.simulate_fmu(filename, start_values={'str_a_': 'string PARAMETER!'}, output=['int_c_'])
        self.assertTrue(np.all(result['int_c_'] == 1))

    def test_tEventRef(self):
        filename = self.fmu_path('fmu_tEventRef.fmu')
        result = fmpy.simulate_fmu(filename, stop_time=1.5, output=['a_'])
        self.assertTrue(result['a_'][-1] == 1)

    def test_variablesRef(self):
        filename = self.fmu_path('fmu_variablesRef.fmu')
        result = fmpy.simulate_fmu(filename, output=['h'])
        self.assertTrue(np.all(result['h'] <= 1.0))

    def test_verRef(self):
        filename = self.fmu_path('fmu_verRef.fmu')
        with self.assertRaises(Exception) as context:
            fmpy.simulate_fmu(filename)
        self.assertEquals(context.exception.message, 'Unsupported FMI version: 2.0.1')
