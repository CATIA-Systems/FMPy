from container_fmu.cli import create_container_fmu
from container_fmu.config import (
    Configuration,
    DefaultExperiment,
    Variable,
    Unit,
    Component,
    Connection,
    FMIMajorVersion,
)
from fmpy.model_description import BaseUnit, DisplayUnit
from fmpy import simulate_fmu, plot_result
from pathlib import Path
from fmpy.fmi3 import (
    fmi3LogMessageCallback,
    fmi3InstanceEnvironment,
    fmi3Status,
    fmi3String,
    printLogMessage,
)


def test_feedthrough(work_dir, reference_fmus_dist_dir):
    configuration = Configuration(
        parallelDoStep=False,
        instantiationToken="",
        fixedStepSize=0.5,
        unitDefinitions=[
            Unit(
                name="rad/s",
                baseUnit=BaseUnit(rad=1, s=-1),
                displayUnits=[DisplayUnit(name="rpm", factor=9.549296585513721)],
            ),
        ],
        # typeDefinitions=[
        #     SimpleType(name='AngularVelocity', type=real_type, quantity='AngularVelocity', unit='rad/s',
        #                displayUnit='rpm'),
        #     SimpleType(name='Option', type='Enumeration', items=[
        #         Item(name='Option 1', value=1, description="First option"),
        #         Item(name='Option 2', value=2, description="Second option")
        #     ])
        # ],
        defaultExperiment=DefaultExperiment(
            startTime="0", stopTime="1", tolerance="1e-5", stepSize="0.1"
        ),
        variables=[
            Variable(
                type="Float64",
                variability="continuous",
                causality="input",
                name="Float64_continuous_input",
                start=["1.1"],
                # declaredType="AngularVelocity",
                mappings=[("instance1", "Float64_continuous_input")],
            ),
            # Variable(
            #     type="Int32",
            #     variability="discrete",
            #     causality="input",
            #     name="Int32_input",
            #     start="2",
            #     mapping=[("instance1", "Int32_input")],
            # ),
            # Variable(
            #     type="Boolean",
            #     variability="discrete",
            #     causality="input",
            #     name="Boolean_input",
            #     start="true",
            #     mapping=[("instance1", "Boolean_input")],
            # ),
            # Variable(
            #     type="Enumeration",
            #     variability="discrete",
            #     causality="input",
            #     name="Enumeration_input",
            #     declaredType="Option",
            #     start="1",
            #     mapping=[("instance1", "Enumeration_input")],
            # ),
            Variable(
                type="Float64",
                initial="calculated",
                variability="continuous",
                causality="output",
                name="Float64_continuous_output",
                # unit="rad/s",
                # displayUnit="rpm",
                mappings=[("instance2", "Float64_continuous_output")],
            ),
            # Variable(
            #     type="Int32",
            #     variability="discrete",
            #     causality="output",
            #     name="Int32_output",
            #     mapping=[("instance2", "Int32_output")],
            # ),
            # Variable(
            #     type="Boolean",
            #     variability="discrete",
            #     causality="output",
            #     name="Boolean_output",
            #     mapping=[("instance2", "Boolean_output")],
            # ),
            # Variable(
            #     type="Enumeration",
            #     variability="discrete",
            #     causality="output",
            #     declaredType="Option",
            #     name="Enumeration_output",
            #     mapping=[("instance2", "Enumeration_output")],
            # ),
        ],
        components=[
            Component(
                fmiMajorVersion=FMIMajorVersion.FMIMajorVersion3,
                name="instance1",
                filename=reference_fmus_dist_dir / "3.0" / "Feedthrough.fmu",
            ),
            Component(
                fmiMajorVersion=FMIMajorVersion.FMIMajorVersion3,
                name="instance2",
                filename=reference_fmus_dist_dir / "3.0" / "Feedthrough.fmu",
            ),
        ],
        connections=[
            Connection(
                "instance1",
                ["Float64_continuous_output"],
                "instance2",
                ["Float64_continuous_input"],
            ),
        ],
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
