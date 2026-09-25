import zipfile

import numpy as np
import pytest

from fmpy.ssp.simulation import simulate_ssp


SSD = """<?xml version="1.0" encoding="UTF-8"?>
<ssd:SystemStructureDescription
    xmlns:ssd="http://ssp-standard.org/SSP1/SystemStructureDescription"
    xmlns:ssc="http://ssp-standard.org/SSP1/SystemStructureCommon"
    name="Dahlquist" version="1.0">
  <ssd:System name="Dahlquist">
    <ssd:Connectors>
      <ssd:Connector name="x" kind="output"><ssc:Real/></ssd:Connector>
    </ssd:Connectors>
    <ssd:Elements>
      <ssd:Component name="model" type="application/x-fmu-sharedlibrary"
                     source="resources/Dahlquist.fmu" implementation="CoSimulation">
        <ssd:Connectors>
          <ssd:Connector name="x" kind="output"><ssc:Real/></ssd:Connector>
        </ssd:Connectors>
      </ssd:Component>
    </ssd:Elements>
    <ssd:Connections>
      <ssd:Connection startElement="model" startConnector="x" endConnector="x"/>
    </ssd:Connections>
  </ssd:System>
  <ssd:DefaultExperiment startTime="0.0" stopTime="10.0"/>
</ssd:SystemStructureDescription>
"""


@pytest.fixture(scope='module')
def dahlquist_ssp(reference_fmus_dist_dir, work_dir):
    """A single-component SSP around the Dahlquist reference FMU."""

    ssp_filename = work_dir / 'Dahlquist.ssp'

    with zipfile.ZipFile(ssp_filename, 'w', zipfile.ZIP_DEFLATED) as ssp:
        ssp.writestr('SystemStructure.ssd', SSD)
        ssp.write(reference_fmus_dist_dir / '2.0' / 'Dahlquist.fmu',
                  'resources/Dahlquist.fmu')

    yield ssp_filename


def test_sample_times(dahlquist_ssp):
    """The grid is start_time .. stop_time inclusive, with no drift."""

    start_time, stop_time, step_size = 0.0, 10.0, 0.1

    result = simulate_ssp(str(dahlquist_ssp), start_time=start_time,
                          stop_time=stop_time, step_size=step_size)

    expected = start_time + np.arange(101) * step_size

    assert len(result) == 101, "one sample per step, plus the initial state"
    assert result['time'][0] == start_time
    assert result['time'][-1] == stop_time
    assert np.all(np.abs(result['time'] - expected) < 1e-12)


def test_sample_values_are_at_their_sample_time(dahlquist_ssp):
    """Each row holds the state AT its own time, not one step earlier.

    Dahlquist is `der(x) = -k * x` with `k = 1` and `x0 = 1`, and the reference
    FMU integrates it with forward Euler at the communication step size, so the
    value at `t = n * h` is exactly `(1 - h) ** n`.
    """

    step_size = 0.1

    result = simulate_ssp(str(dahlquist_ssp), start_time=0.0, stop_time=10.0,
                          step_size=step_size)

    expected = (1.0 - step_size) ** np.arange(101)

    assert result['x'][0] == 1.0, "the first row is the initial state"
    assert np.all(np.abs(result['x'] - expected) < 1e-12)
