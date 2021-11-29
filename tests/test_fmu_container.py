import os
import unittest
from fmpy import simulate_fmu, plot_result
from fmpy.fmucontainer import create_fmu_container, Variable, Connection, Configuration, Component, Unit, BaseUnit, DisplayUnit, SimpleType
from fmpy.validation import validate_fmu
import numpy as np


@unittest.skipIf('SSP_STANDARD_DEV' not in os.environ, "Environment variable SSP_STANDARD_DEV must point to the clone of https://github.com/modelica/ssp-standard-dev")
class FMUContainerTest(unittest.TestCase):

    def test_create_fmu_container(self):

        examples = os.path.join(os.environ['SSP_STANDARD_DEV'], 'SystemStructureDescription', 'examples')

        configuration = Configuration(
            description="A controlled drivetrain",
            variableNamingConvention='structured',
            unitDefinitions=[
                Unit(name='rad/s', baseUnit=BaseUnit(rad=1, s=-1), displayUnits=[DisplayUnit(name='rpm', factor=0.1047197551196598)])
            ],
            typeDefinitions=[
                SimpleType(name='AngularVelocity', type='Real', unit='rad/s')
            ],
            variables=[
                    Variable(
                        type='Real',
                        variability='tunable',
                        causality='parameter',
                        name='k',
                        start='100',
                        description='Gain of controller',
                        mapping=[('controller', 'PI.k')]
                    ),
                    Variable(
                        type='Real',
                        variability='continuous',
                        causality='input',
                        name='w_ref',
                        start='0',
                        description='Reference speed',
                        mapping=[('controller', 'u_s')],
                        declaredType='AngularVelocity'
                    ),
                    Variable(
                        type='Real',
                        variability='continuous',
                        causality='output',
                        name='w',
                        description="Gain of controller",
                        mapping=[('drivetrain', 'w')],
                        unit='rad/s',
                        displayUnit='rpm'
                    ),
                ],
            components=[
                    Component(
                        filename=os.path.join(examples, 'Controller.fmu'),
                        name='controller'
                    ),
                    Component(
                        filename=os.path.join(examples, 'Drivetrain.fmu'),
                        name='drivetrain',
                    )
                ],
            connections=[
                Connection('drivetrain', 'w', 'controller', 'u_m'),
                Connection('controller', 'y', 'drivetrain', 'tau'),
            ]
        )

        filename = 'ControlledDrivetrain.fmu'

        create_fmu_container(configuration, filename)

        problems = validate_fmu(filename)

        self.assertEqual(problems, [])

        w_ref = np.array([(0.5, 0), (1.5, 1), (2, 1), (3, 0)], dtype=[('time', 'f8'), ('w_ref', 'f8')])

        result = simulate_fmu(filename, start_values={'k': 20}, input=w_ref, output=['w_ref', 'w'], stop_time=4)

        plot_result(result)
