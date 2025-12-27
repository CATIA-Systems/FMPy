from fmpy import simulate_fmu, read_model_description
from fmpy.container_fmu.cli import create_container_fmu
from fmpy.container_fmu.config import Configuration, Component, Connection
from fmpy.fmi3 import (

    printLogMessage,
)
from fmpy.model_description import BaseUnit, DisplayUnit, ModelDescription, SimpleType, Item, DefaultExperiment, \
    ModelVariable, Unit, CoSimulation


def test_feedthrough(work_dir, reference_fmus_dist_dir):

    container_input = ModelVariable(
        type="Float64",
        variability="continuous",
        causality="input",
        name="Float64_continuous_input",
        start="1.1",
    )

    container_output = ModelVariable(
        type="Float64",
        initial="calculated",
        variability="continuous",
        causality="output",
        name="Float64_continuous_output",
    )

    model_description = ModelDescription(
        fmiVersion="3.0.2",
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
            SimpleType(name='AngularVelocity', type="Float64", quantity='AngularVelocity', unit='rad/s',
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
                type="Float64",
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

    result = simulate_fmu(
        filename,
        debug_logging=True,
        fmi_call_logger=print,
        logger=printLogMessage,
        output_interval=0.5,
        stop_time=1,
        start_values={"Float64_continuous_input": 1.5},
    )

    print(result)
