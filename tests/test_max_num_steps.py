import pytest

from fmpy import simulate_fmu


def test_max_num_steps_is_reachable(reference_fmus_dist_dir):
    """ max_num_steps must reach CVode.

    An absurdly low limit has to stop the simulation; without the parameter
    being plumbed through, it would be ignored and the run would succeed.
    """

    filename = reference_fmus_dist_dir / '2.0' / 'VanDerPol.fmu'

    with pytest.raises(RuntimeError) as excinfo:
        simulate_fmu(filename,
                     fmi_type='ModelExchange',
                     start_time=0.0,
                     stop_time=10.0,
                     output_interval=1.0,
                     relative_tolerance=1e-8,
                     output=['x0'],
                     max_num_steps=1)

    message = str(excinfo.value)
    assert 'internal steps' in message, message
    # the message has to say what to do about it
    assert 'max_num_steps' in message and 'output_interval' in message, message


def test_default_max_num_steps_is_unchanged(reference_fmus_dist_dir):
    """ Not passing max_num_steps must leave the previous behaviour in place. """

    filename = reference_fmus_dist_dir / '2.0' / 'VanDerPol.fmu'

    kwargs = dict(fmi_type='ModelExchange', start_time=0.0, stop_time=10.0,
                  output_interval=0.01, relative_tolerance=1e-6, output=['x0'])

    default = simulate_fmu(filename, **kwargs)
    explicit = simulate_fmu(filename, max_num_steps=500, **kwargs)

    assert len(default) == len(explicit)
    assert (default['x0'] == explicit['x0']).all()
