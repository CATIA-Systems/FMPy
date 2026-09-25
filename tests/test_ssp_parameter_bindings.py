import zipfile

import numpy as np
import pytest

from fmpy.ssp.simulation import simulate_ssp


SSD = """<?xml version="1.0" encoding="UTF-8"?>
<ssd:SystemStructureDescription
    xmlns:ssd="http://ssp-standard.org/SSP1/SystemStructureDescription"
    xmlns:ssc="http://ssp-standard.org/SSP1/SystemStructureCommon"
    xmlns:ssv="http://ssp-standard.org/SSP1/SystemStructureParameterValues"
    name="Feedthrough" version="1.0">
  <ssd:System name="Feedthrough">
    <ssd:Connectors>
      <ssd:Connector name="y" kind="output"><ssc:Real/></ssd:Connector>
    </ssd:Connectors>
    <ssd:Elements>
      <ssd:Component name="model" type="application/x-fmu-sharedlibrary"
                     source="resources/Feedthrough.fmu" implementation="CoSimulation">
        <ssd:Connectors>
          <ssd:Connector name="Float64_continuous_output" kind="output"><ssc:Real/></ssd:Connector>
        </ssd:Connectors>
        %s
      </ssd:Component>
    </ssd:Elements>
    <ssd:Connections>
      <ssd:Connection startElement="model" startConnector="Float64_continuous_output"
                      endConnector="y"/>
    </ssd:Connections>
  </ssd:System>
  <ssd:DefaultExperiment startTime="0.0" stopTime="1.0"/>
</ssd:SystemStructureDescription>
"""

BINDING = """<ssd:ParameterBindings>
          <ssd:ParameterBinding>
            <ssd:ParameterValues>
              <ssv:ParameterSet version="1.0" name="values">
                <ssv:Parameters>
                  <ssv:Parameter name="Float64_continuous_input">
                    <ssv:Real value="42.0"/>
                  </ssv:Parameter>
                  <ssv:Parameter name="not_a_variable_of_this_fmu">
                    <ssv:Real value="1.0"/>
                  </ssv:Parameter>
                </ssv:Parameters>
              </ssv:ParameterSet>
            </ssd:ParameterValues>
          </ssd:ParameterBinding>
        </ssd:ParameterBindings>"""


def _build(path, reference_fmus_dist_dir, parameter_bindings):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as ssp:
        ssp.writestr('SystemStructure.ssd', SSD % parameter_bindings)
        ssp.write(reference_fmus_dist_dir / '2.0' / 'Feedthrough.fmu',
                  'resources/Feedthrough.fmu')
    return path


def test_inline_parameter_set_is_applied(reference_fmus_dist_dir, work_dir):
    """The SSD's own parameter values reach the FMU.

    Feedthrough's continuous output follows its continuous input, and nothing
    in this SSP is connected to that input, so the start value the parameter
    binding sets is what comes out -- at every sample.
    """

    ssp_filename = _build(work_dir / 'Feedthrough_bound.ssp',
                          reference_fmus_dist_dir, BINDING)

    result = simulate_ssp(str(ssp_filename), stop_time=1.0, step_size=0.1)

    assert np.all(result['y'] == 42.0)


def test_without_a_binding_the_fmu_default_stands(reference_fmus_dist_dir, work_dir):
    """The control: the same SSP with no parameter binding at all."""

    ssp_filename = _build(work_dir / 'Feedthrough_unbound.ssp',
                          reference_fmus_dist_dir, '')

    result = simulate_ssp(str(ssp_filename), stop_time=1.0, step_size=0.1)

    assert np.all(result['y'] == 0.0)
