import pytest
import numpy as np
from fmpy import simulate_fmu, platform_tuple
from fmpy.util import download_test_file, download_file


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_step_size_cs():

    url = 'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win64/Test-FMUs/0.0.2/Dahlquist/Dahlquist.fmu'
    sha256 = '6df6ab64705615dfa1217123a103c23384a081763a6f71726ba7943503da8fc0'

    filename = download_file(url, checksum=sha256)

    h = 0.02

    result = simulate_fmu(filename, output_interval=h, stop_time=10)

    time = result['time']

    grid = np.array(range(501)) * h

    assert np.all(time == grid)

@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_step_size_me():

    # download the FMU and input file
    for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
        download_test_file('2.0', 'me', 'MapleSim', '2016.2', 'CoupledClutches', filename)

    # load the input
    input = np.genfromtxt('CoupledClutches_in.csv', delimiter=',', names=True)

    assert np.sum(input['time'] == 0.9) > 1, "Input event expected at t=0.9"

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
    assert time[0] == pytest.approx(start_time), "First sample time must be equal to start_time"
    assert time[-1] == pytest.approx(stop_time), "Last sample time must be equal to stop_time"
    assert np.all(np.isclose(np.diff(time), output_interval)), "Output intervals must be regular"

    # fixed step w/ events
    result = simulate_fmu(solver='Euler', record_events=True, **kwargs)

    time = result['time']
    assert time[0] == pytest.approx(start_time), "First sample time must be equal to start_time"
    assert time[-1] == pytest.approx(stop_time), "Last sample time must be equal to stop_time"

    # variable step w/o events
    result = simulate_fmu(solver='CVode', record_events=False, **kwargs)

    time = result['time']
    assert time[0] == pytest.approx(start_time), "First sample time must be equal to start_time"
    assert time[-1] == pytest.approx(stop_time), "Last sample time must be equal to stop_time"
    steps = np.diff(time)
    steps = steps[steps > 1e-13]  # remove events
    assert np.all(np.isclose(steps, output_interval)), "Output intervals must be regular"

    # variable step w/ events
    result = simulate_fmu(solver='CVode', record_events=True, **kwargs)

    time = result['time']
    assert time[0] == pytest.approx(start_time), "First sample time must be equal to start_time"
    assert time[-1] == pytest.approx(stop_time), "Last sample time must be equal to stop_time"
    assert np.sum(time == 0.9) > 1, "Input event expected at t=0.9"
    assert np.sum(np.isclose(time, T2)) > 1, "Time event expected at t=T2"
