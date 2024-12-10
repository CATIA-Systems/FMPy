import pytest
from fmpy import dump, simulate_fmu
from fmpy.util import fmu_info


def test_illegal_fmi_type(reference_fmus_dist_dir):

    filename = reference_fmus_dist_dir / '2.0' / 'BouncingBall.fmu'

    with pytest.raises(Exception) as context:
        simulate_fmu(filename, fmi_type='Hybrid')

    assert 'fmi_type must be one of "ModelExchange" or "CoSimulation"' == str(context.value)

def test_unsupported_fmi_type(reference_fmus_dist_dir):

    filename = reference_fmus_dist_dir / '1.0' / 'me' / 'BouncingBall.fmu'

    with pytest.raises(Exception) as context:
        simulate_fmu(filename, fmi_type='CoSimulation')

    assert 'FMI type "CoSimulation" is not supported by the FMU' == str(context.value)

def test_fmu_info(reference_fmus_dist_dir):

    filename = reference_fmus_dist_dir / '2.0' / 'BouncingBall.fmu'

    info = fmu_info(filename)

    generation_dates = {
        'darwin64': '2017-01-19T17:56:19Z',
        'linux64':  '2017-01-19T18:38:03Z',
        'win32':    '2017-01-19T18:48:24Z',
        'win64':    '2017-01-19T18:42:35Z',
    }

    expected = """
Model Info

  FMI Version        2.0
  FMI Type           Model Exchange, Co-Simulation
  Model Name         BouncingBall
  Description        This model calculates the trajectory, over time, of a ball dropped from a height of 1 m.
  Platforms          c-code, darwin64, linux64, win64
  Continuous States  2
  Event Indicators   1
  Variables          8
  Generation Tool    Reference FMUs (v0.0.25)
  Generation Date    2023-08-04T08:43:49.469027+00:00

Default Experiment

  Stop Time          3.0
  Step Size          0.01

Variables (input, output)

  Name               Causality              Start Value  Unit     Description
  h                  output                           1  m        Position of the ball
  v                  output                           0  m/s      Velocity of the ball"""

    assert expected == info

def test_dump(reference_fmus_dist_dir):

    filename = reference_fmus_dist_dir / '2.0' / 'BouncingBall.fmu'

    # dump the FMU info
    dump(filename)
