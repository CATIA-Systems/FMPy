from fmpy import simulate_fmu, plot_result
from fmpy.fmucontainer import create_fmu_container, Variable, Connection, Configuration, Component, Unit, BaseUnit, DisplayUnit, SimpleType
from fmpy.validation import validate_fmu
from fmpy.util import validate_signal, read_csv
import numpy as np


def test_create_fmu_container_me(resources_dir):

    configuration = Configuration(
        parallelDoStep=False,
        variables=[
            Variable(
                type='Real',
                variability='continuous',
                causality='output',
                initial='calculated',
                name='h',
                description='Height',
                mapping=[('ball', 'h')]
            ),
            Variable(
                type='Boolean',
                variability='discrete',
                causality='output',
                initial='calculated',
                name='reset',
                description="Reset",
                mapping=[('bounce', 'reset')]
            ),
            Variable(
                type='Real',
                variability='discrete',
                causality='output',
                initial='calculated',
                name='ticks',
                description='Ticks',
                mapping=[('ticker', 'ticks')]
            ),
        ],
        components=[
            Component(
                filename=resources_dir / 'Bounce.fmu',
                interfaceType='ModelExchange',
                name='bounce'
            ),
            Component(
                filename=resources_dir / 'Ball.fmu',
                interfaceType='ModelExchange',
                name='ball'
            ),
            Component(
                filename=resources_dir / 'Ticker.fmu',
                interfaceType='ModelExchange',
                name='ticker'
            )
        ],
        connections=[
            Connection('ball', 'h', 'bounce', 'h'),
            Connection('bounce', 'reset', 'ball', 'reset'),
        ]
    )

    filename = 'BouncingAndBall.fmu'

    create_fmu_container(configuration, filename)

    problems = validate_fmu(filename)

    assert not problems

    result = simulate_fmu(filename, stop_time=3.5, fmi_call_logger=None)

    # plot_result(result)


def test_create_fmu_container_cs(resources_dir):

    configuration = Configuration(
        parallelDoStep=True,
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
                initial='exact',
                name='k',
                start='40',
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
                initial='calculated',
                name='w',
                description="Gain of controller",
                mapping=[('drivetrain', 'w')],
                unit='rad/s',
                displayUnit='rpm'
            ),
        ],
        components=[
            Component(
                filename=resources_dir / 'Controller.fmu',
                interfaceType='CoSimulation',
                name='controller'
            ),
            Component(
                filename=resources_dir / 'Drivetrain.fmu',
                interfaceType='CoSimulation',
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

    assert not problems

    input = read_csv(resources_dir / 'ControlledDrivetrain_in.csv')

    result = simulate_fmu(filename, input=input, output=['w_ref', 'w', 'k'], stop_time=5, output_interval=5e-2)

    t_band, y_min, y_max, i_out = validate_signal(t=result['time'], y=result['w'],
                                                  t_ref=input['time'], y_ref=input['w_ref'], dx=100, dy=0.4)

    assert result['k'][0] == 40, 'Default start value has not been set.'

    assert not i_out.any()

    # plot_result(result)
