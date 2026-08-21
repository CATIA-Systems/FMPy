import unittest
from fmpy.examples import optimize_eggholder_function as example
import fmpy
import os


class TestOptimizeEggholderFunction(unittest.TestCase):

    def test_eggholder(self):
        self.assertEqual(example.eggholder([0, 0]), -25.460337185286313)

    def test_simulate_eggholder_fmu(self):
        unzipdir = fmpy.extract(os.path.join(os.path.dirname(__file__), 'resources', 'eggholder.fmu'))
        model_description = fmpy.read_model_description(unzipdir)

        self.assertEqual(example.simulate_eggholder_fmu(x=[0, 0], unzipdir=unzipdir, model_description=model_description), -25.460337185286313)

    def test_optimize_eggholder_fmu(self):

        res = example.optimize_eggholder(method='differential_evolution', use_fmu=True)
        self.assertEqual(res.fun, -959.640662720845)

        res = example.optimize_eggholder(method='shgo', use_fmu=True)
        self.assertEqual(res.fun, -959.6406627208441)

        res = example.optimize_eggholder(method='dual_annealing', use_fmu=True)
        self.assertEqual(res.fun, -959.6406627208398)

        res = example.optimize_eggholder(method='differential_evolution', use_fmu=False)
        self.assertEqual(res.fun, -959.640662720845)

        res = example.optimize_eggholder(method='shgo', use_fmu=False)
        self.assertEqual(res.fun, -959.6406627208441)

        res = example.optimize_eggholder(method='dual_annealing', use_fmu=False)
        self.assertEqual(res.fun, -959.6406627208398)

    def test_optimize_eggholder_fmu_ValueError(self):

        self.assertRaises(ValueError, example.optimize_eggholder, 'unknown method')