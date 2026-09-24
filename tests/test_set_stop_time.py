import numpy as np
import pytest

from fmpy import instantiate_fmu, extract, read_model_description, simulate_fmu


# FMI 1.0 Model Exchange has no way to declare a stop time to the FMU, so there
# is no bound to honour there and set_stop_time does not apply.
@pytest.mark.parametrize('fmi_version', ['2.0', '3.0'])
def test_solver_stays_inside_the_declared_stop_time(reference_fmus_dist_dir, fmi_version):
    """ With set_stop_time=True the model must not be evaluated beyond stop_time.

    The specification is explicit: "If the environment tries to compute past
    stopTime, the FMU has to return fmi3Status = fmi3Error" (FMI 3.0, and the
    same sentence in FMI 2.0 for fmi2SetupExperiment). CVode integrates past
    tout and interpolates back, so without CVodeSetStopTime() the right-hand
    side is called beyond the stop time that was just declared, and an FMU that
    implements the requirement fails the simulation.
    """

    stop_time = 3.0

    filename = reference_fmus_dist_dir / fmi_version / 'VanDerPol.fmu'

    model_description = read_model_description(filename)
    unzipdir = extract(filename)
    fmu = instantiate_fmu(unzipdir, model_description, 'ModelExchange')

    times = []
    set_time = fmu.setTime

    def record(time, *args, **kwargs):
        times.append(time)
        return set_time(time, *args, **kwargs)

    fmu.setTime = record

    simulate_fmu(filename,
                 start_time=0.0,
                 stop_time=stop_time,
                 output_interval=0.01,
                 relative_tolerance=1e-6,
                 fmi_type='ModelExchange',
                 output=['x0'],
                 model_description=model_description,
                 fmu_instance=fmu,
                 set_stop_time=True)

    # simulate_fmu() terminates an instance it was handed; only the freeing is
    # left to the caller.
    fmu.freeInstance()

    assert times, "the model was never evaluated"
    assert max(times) <= stop_time, \
        f"the model was evaluated at t={max(times)}, beyond the declared stop time {stop_time}"


@pytest.mark.parametrize('fmi_version', ['1.0', '2.0', '3.0'])
def test_declaring_the_stop_time_does_not_change_the_result(reference_fmus_dist_dir, fmi_version):
    """ set_stop_time is a statement about the experiment, not a solver setting,
    so turning it on must not move the trajectory. """

    stop_time = 3.0

    if fmi_version == '1.0':
        filename = reference_fmus_dist_dir / '1.0' / 'me' / 'BouncingBall.fmu'
    else:
        filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    kwargs = dict(start_time=0.0, stop_time=stop_time, output_interval=0.01,
                  relative_tolerance=1e-8, fmi_type='ModelExchange', output=['h'])

    on = simulate_fmu(filename, set_stop_time=True, **kwargs)
    off = simulate_fmu(filename, set_stop_time=False, **kwargs)

    assert len(on) == len(off)
    assert on['time'][-1] == pytest.approx(stop_time, abs=1e-9)
    assert np.max(np.abs(on['h'] - off['h'])) < 1e-6
