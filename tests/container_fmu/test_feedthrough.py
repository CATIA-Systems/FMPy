import numpy as np
import pytest

from fmpy import simulate_fmu, read_model_description, read_csv, platform_tuple
from fmpy.container_fmu.cli import create_container_fmu
from fmpy.container_fmu.config import Configuration, Component, Connection
from fmpy.fmi3 import (

    printLogMessage,
)
from fmpy.model_description import BaseUnit, DisplayUnit, ModelDescription, SimpleType, Item, DefaultExperiment, \
    ModelVariable, Unit, CoSimulation


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="FMI 2.0 does not support aarch64-darwin")
def test_feedthrough(work_dir, reference_fmus_dist_dir, resources_dir):

    container_input = ModelVariable(
        type="Real",
        variability="continuous",
        causality="input",
        name="Float64_continuous_input",
        start="1.1",
    )

    container_output = ModelVariable(
        type="Real",
        initial="calculated",
        variability="continuous",
        causality="output",
        name="Float64_continuous_output",
    )

    model_description = ModelDescription(
        fmiVersion="2.0",
        modelName="Feedthrough",
        instantiationToken="",
        unitDefinitions=[
            Unit(
                name="rad/s",
                baseUnit=BaseUnit(rad=1, s=-1),
                displayUnits=[DisplayUnit(name="rpm", factor=9.549296585513721)],
            ),
        ],
        typeDefinitions=[
            SimpleType(name='AngularVelocity', type="Real", quantity='AngularVelocity', unit='rad/s',
                       displayUnit='rpm'),
            SimpleType(name='Option', type='Enumeration', items=[
                Item(name='Option 1', value="1", description="First option"),
                Item(name='Option 2', value="2", description="Second option")
            ])
        ],
        defaultExperiment=DefaultExperiment(
            stopTime="1", stepSize="0.1"
        ),
        coSimulation=CoSimulation(
            fixedInternalStepSize=0.1
        ),
        modelVariables=[
            ModelVariable(
                type="Real",
                variability="continuous",
                causality="independent",
                name="time",
            ),
            container_input,
            container_output
        ]
    )

    component_model_description = read_model_description(reference_fmus_dist_dir / "3.0" / "Feedthrough.fmu")

    component_variables: dict[str, ModelVariable] = dict(map(lambda v: (v.name, v), component_model_description.modelVariables))

    instance1 = Component(
        name="instance1",
        filename=reference_fmus_dist_dir / "3.0" / "Feedthrough.fmu",
        modelDescription=component_model_description,
    )

    instance2 = Component(
        name="instance2",
        filename=reference_fmus_dist_dir / "3.0" / "Feedthrough.fmu",
        modelDescription=component_model_description,
    )

    configuration = Configuration(
        parallelDoStep=False,
        modelDescription=model_description,
        components=[
            instance1,
            instance2
        ],
        connections=[
            Connection(
                instance1,
                [component_variables["Float64_continuous_output"]],
                instance2,
                [component_variables["Float64_continuous_input"]],
            ),
        ],
        variableMappings={
            container_input: [(instance1, component_variables["Float64_continuous_input"])],
            container_output: [(instance2, component_variables["Float64_continuous_output"])],
        }
    )

    unzipdir = work_dir

    filename = unzipdir / "Container.fmu"

    create_container_fmu(configuration, unzipdir, filename)

    input = np.array(
        [
            (0.0, 0.0),
            (1.0, 1.0),
        ],
        dtype=[
            ('time', 'f8'),
            ('Float64_continuous_input', 'f8')
        ]
    )

    result = simulate_fmu(
        filename,
        debug_logging=True,
        fmi_call_logger=print,
        logger=printLogMessage,
        output_interval=0.5,
        stop_time=1,
        # start_values={"Float64_continuous_input": 1.5},
        input=input
    )

    print(result)
