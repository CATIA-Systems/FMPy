import os.path

import pytest
from fmpy.examples.coupled_clutches import simulate_coupled_clutches
from fmpy.examples.custom_input import simulate_custom_input
from fmpy.examples.efficient_loops import run_efficient_loop
from fmpy.examples.parameter_variation import run_experiment
from fmpy.examples.continue_simulation import continue_simulation
from fmpy import platform, platform_tuple
import numpy as np


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_coupled_clutches_example():

    if platform.startswith('win'):
        fmi_versions = ['2.0']  # ['1.0', '2.0'] quick fix until 1.0 is available again
    elif platform.startswith(('darwin', 'linux')):
        fmi_versions = ['2.0']
    else:
        pytest.fail('Platform not supported')

    for fmi_version in fmi_versions:
        for fmi_type in ['CoSimulation', 'ModelExchange']:

            solvers = ['Euler']

            if fmi_type == 'ModelExchange':
                solvers.append('CVode')

            for solver in solvers:

                result = simulate_coupled_clutches(fmi_version=fmi_version,
                                                   fmi_type=fmi_type,
                                                   solver=solver,
                                                   show_plot=False,
                                                   output=['inputs', 'CoupledClutches1_freqHz'])

                if result is not None:  # sometimes the download fails...

                    freqHz = result['CoupledClutches1_freqHz']
                    assert np.all(freqHz == 0.4), "Start value has not been applied"

                    inputs = result['inputs']
                    assert inputs[0] == pytest.approx(0), "Input has not been applied"
                    assert inputs[-1] == pytest.approx(1), "Input has not been applied"

                    assert 0.0 == result['time'][0], "Result must start at start_time (= 0.0)"


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_custom_input_example():
    end_time = simulate_custom_input(show_plot=False)
    assert end_time == pytest.approx(1.1, rel=1e-2)


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_efficient_loops():
    run_efficient_loop()


@pytest.mark.skipif(platform not in ['win32', 'win64'], reason="FMU only available for Windows")
def test_parameter_variation():
    LOSSES = run_experiment(show_plot=False)
    assert np.all(LOSSES > 0)


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_continue_simulation(reference_fmus_dist_dir):
    for fmi_version in ['1.0/cs', '2.0', '3.0']:
        continue_simulation(fmu_filename=os.path.join(reference_fmus_dist_dir, fmi_version, 'BouncingBall.fmu'))
