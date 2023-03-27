import os.path
import pytest
from itertools import product
from fmpy import simulate_fmu, plot_result
from fmpy.fmucontainer import create_fmu_container, Variable, Connection, Configuration, Component
from fmpy.util import compile_platform_binary
from fmpy.validation import validate_fmu


@pytest.mark.parametrize('fmi_version, parallelDoStep', product([2, 3], [False, True]))
def test_create_fmu_container(reference_fmus_dist_dir, fmi_version: int, parallelDoStep: bool):

    if fmi_version == 2:
        real_type = 'Real'
        integer_type = 'Integer'
    else:
        real_type = 'Float64'
        integer_type = 'Int32'

    fmi_version_str = f'{fmi_version}.0',
    configuration = Configuration(
        fmiVersion=fmi_version_str,
        parallelDoStep=parallelDoStep,
        variables=[
            Variable(
                type=real_type,
                variability='continuous',
                causality='input',
                name='Float64_continuous_input',
                start='1.1',
                mapping=[('instance1', 'Float64_continuous_input')]
            ),
            Variable(
                type=integer_type,
                variability='discrete',
                causality='input',
                name='Int32_input',
                start='2',
                mapping=[('instance1', 'Int32_input')]
            ),
            Variable(
                type='Boolean',
                variability='discrete',
                causality='input',
                name='Boolean_input',
                start='true',
                mapping=[('instance1', 'Boolean_input')]
            ),
            Variable(
                type=real_type,
                initial='calculated',
                variability='continuous',
                causality='output',
                name='Float64_continuous_output',
                mapping=[('instance2', 'Float64_continuous_output')]
            ),
            Variable(
                type=integer_type,
                variability='discrete',
                causality='output',
                name='Int32_output',
                mapping=[('instance2', 'Int32_output')]
            ),
            Variable(
                type='Boolean',
                variability='discrete',
                causality='output',
                name='Boolean_output',
                mapping=[('instance2', 'Boolean_output')]
            ),
        ],
        components=[
            Component(
                filename=os.path.join(reference_fmus_dist_dir, fmi_version_str, 'Feedthrough.fmu'),
                name='instance1'
            ),
            Component(
                filename=os.path.join(reference_fmus_dist_dir, fmi_version_str, 'Feedthrough.fmu'),
                name='instance2'
            ),
        ],
        connections=[
            Connection('instance1', 'Float64_continuous_output', 'instance2', 'Float64_continuous_input'),
            Connection('instance1', 'Int32_output', 'instance2', 'Int32_input'),
            Connection('instance1', 'Boolean_output', 'instance2', 'Boolean_input'),
        ]
    )

    if parallelDoStep:
        filename = f'FeedthroughParallel{fmi_version}.fmu'
    else:
        filename = f'FeedthroughSynchronous{fmi_version}.fmu'

    create_fmu_container(configuration, filename)

    problems = validate_fmu(filename)

    assert not problems

    # test default start values

    default_start_values = {
        'Float64_continuous_input': 1.1,
        'Boolean_input': True,
        'Int32_input': 2,
    }

    result = simulate_fmu(filename, output=default_start_values.keys(),
                          # debug_logging=True,
                          fmi_call_logger=print,
                          stop_time=1, output_interval=1)

    for name, expected in default_start_values.items():
        actual = result[name][0]
        assert actual == expected

    # test custom start values & connections

    custom_start_values = {
        'Float64_continuous_input': 1.2,
        'Boolean_input': False,
        'Int32_input': 3,
    }

    result = simulate_fmu(filename,
                          start_values=custom_start_values,
                          output=['Float64_continuous_input', 'Int32_input', 'Boolean_input',
                                  'Float64_continuous_output', 'Int32_output', 'Boolean_output'],
                          # debug_logging=True,
                          # fmi_call_logger=print,
                          stop_time=1, output_interval=1)

    for name, expected in custom_start_values.items():
        actual = result[name][0]
        assert actual == expected

    assert result['Float64_continuous_output'][-1] == 1.2
    assert result['Int32_output'][-1] == 3
    assert result['Boolean_output'][-1] == False

    compile_platform_binary(filename)
    simulate_fmu(filename=filename)
