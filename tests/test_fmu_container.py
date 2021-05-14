import os
import unittest
from fmpy import simulate_fmu
from fmpy.fmucontainer import create_fmu_container, Variable, Connection
from fmpy.validation import validate_fmu
import numpy as np


@unittest.skipIf('SSP_STANDARD_DEV' not in os.environ, "Environment variable SSP_STANDARD_DEV must point to the clone of https://github.com/modelica/ssp-standard-dev")
class FMUContainerTest(unittest.TestCase):

    def test_create_fmu_container(self):

        examples = os.path.join(os.environ['SSP_STANDARD_DEV'], 'SystemStructureDescription', 'examples')

        configuration = {

            # description of the container
            'description': 'A controlled drivetrain',

            # variables of the container
            'variables':
                [
                    Variable('Real', 'tunable', 'parameter', 'k', '100', 'Gain of controller', [('controller', 'PI.k')]),
                    Variable('Real', 'continuous', 'input', 'w_ref', '0', 'Reference speed', [('controller', 'u_s')]),
                    Variable('Real', 'continuous', 'output', 'w', None, 'Gain of controller', [('drivetrain', 'w')]),
                ],

            # models to include in the container
            'components':
                [
                    {
                        'filename': os.path.join(examples, 'Controller.fmu'),  # filename of the FMU
                        'name': 'controller',  # instance name
                    },
                    {
                        'filename': os.path.join(examples, 'Drivetrain.fmu'),
                        'name': 'drivetrain',
                    }
                ],

            # connections between the FMU instances
            'connections':
                [
                    Connection('drivetrain', 'w', 'controller', 'u_m'),
                    Connection('controller', 'y', 'drivetrain', 'tau'),
                ]

        }

        filename = 'ControlledDrivetrain.fmu'

        create_fmu_container(configuration, filename)

        w_ref = np.array([(0.5, 0), (1.5, 1), (2, 1), (3, 0)], dtype=[('time', 'f8'), ('w_ref', 'f8')])

        problems = validate_fmu(filename)

        self.assertEqual(problems, [])

        result = simulate_fmu(filename, start_values={'k': 20}, input=w_ref, output=['w_ref', 'w'], stop_time=4)
