import unittest
import numpy as np
import sys
from fmpy import simulate_fmu
from fmpy.util import download_test_file


class OutputGridTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("Python:", sys.version)

    def test_step_size(self):

        # download the FMU and input file
        for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
            download_test_file('2.0', 'me', 'MapleSim', '2016.2', 'CoupledClutches', filename)

        # load the input
        input = np.genfromtxt('CoupledClutches_in.csv', delimiter=',', names=True)

        self.assertTrue(np.sum(input['time'] == 0.9) > 1, msg="Input event expected at t=0.9")

        start_time = 0.0
        stop_time = 1.5
        step_size = 1e-2
        output_interval = 2e-2
        T2 = 0.5

        # common arguments
        kwargs = {
            'filename': 'CoupledClutches.fmu',
            'start_time': start_time,
            'stop_time': stop_time,
            'fmi_type': 'ModelExchange',
            'step_size': step_size,
            'output_interval': output_interval,
            'input': input,
            'start_values': {'CoupledClutches1_T2': T2}
        }

        # fixed step w/o events
        result = simulate_fmu(solver='Euler', record_events=False, **kwargs)

        time = result['time']
        self.assertAlmostEqual(time[0], start_time, msg="First sample time must be equal to start_time")
        self.assertAlmostEqual(time[-1], stop_time, msg="Last sample time must be equal to stop_time")
        self.assertTrue(np.all(np.isclose(np.diff(time), output_interval)), msg="Output intervals must be regular")

        # fixed step w/ events
        result = simulate_fmu(solver='Euler', record_events=True, **kwargs)

        time = result['time']
        self.assertAlmostEqual(time[0], start_time, msg="First sample time must be equal to start_time")
        self.assertAlmostEqual(time[-1], stop_time, msg="Last sample time must be equal to stop_time")

        # variable step w/o events
        result = simulate_fmu(solver='CVode', record_events=False, **kwargs)

        time = result['time']
        self.assertAlmostEqual(time[0], start_time, msg="First sample time must be equal to start_time")
        self.assertAlmostEqual(time[-1], stop_time, msg="Last sample time must be equal to stop_time")
        self.assertTrue(np.all(np.isclose(np.diff(time), output_interval)), msg="Output intervals must be regular")

        # variable step w/ events
        result = simulate_fmu(solver='CVode', record_events=True, **kwargs)

        time = result['time']
        self.assertAlmostEqual(time[0], start_time, msg="First sample time must be equal to start_time")
        self.assertAlmostEqual(time[-1], stop_time, msg="Last sample time must be equal to stop_time")
        self.assertTrue(np.sum(time == 0.9) > 1, msg="Input event expected at t=0.9")
        self.assertTrue(np.sum(np.isclose(time, T2)) > 1, msg="Time event expected at t=T2")
