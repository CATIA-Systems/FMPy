import fmpy
import uuid

import shutil

from datetime import datetime, timezone
from os import makedirs, PathLike
from pathlib import Path
from subprocess import check_call
from tempfile import TemporaryDirectory

import jinja2
from .model_description import ModelDescription, CoSimulation, DefaultExperiment, ScalarVariable, Unknown, ModelVariable
from .util import create_zip_archive


def create_fmu(model_description: ModelDescription, filename: str | PathLike = None) -> None:

    with TemporaryDirectory() as unzipdir:

        unzipdir = Path(unzipdir)

        template_dir = Path(__file__).parent / 'templates'

        loader = jinja2.FileSystemLoader(searchpath=template_dir)

        environment = jinja2.Environment(loader=loader, trim_blocks=True)

        xml_template = environment.get_template('modelDescription.xml')

        xml = xml_template.render(
            modelDescription=model_description,
        )

        c_template = environment.get_template('model.c')

        c = c_template.render(
            modelDescription=model_description,
            fmpyVersion=fmpy.__version__,
        )

        with open(unzipdir / "modelDescription.xml", "w") as xml_file:
            xml_file.write(xml)

        makedirs(unzipdir / "sources", exist_ok=True)

        with open(unzipdir / "sources" / "model.c", "w") as c_file:
            c_file.write(c)

        shutil.copy(src=template_dir / "buildDescription.xml", dst=unzipdir / "sources" / "buildDescription.xml")

        create_zip_archive(filename, unzipdir)


def main() -> None:

    model_description = ModelDescription()

    model_description.modelName = 'foo'
    model_description.description = 'description'

    model_description.coSimulation = CoSimulation(modelIdentifier="bb")

    model_description.defaultExperiment = DefaultExperiment(
        startTime="0.0",
        stopTime="1.0",
        stepSize="1e-3"
    )

    time = ScalarVariable(
        name="time",
        valueReference=0,
        causality='independent',
        variability='continuous',
        description="description"
    )

    real_in = ScalarVariable(
        name="real_in",
        valueReference=10,
        start='0',
        causality='input',
        variability='continuous',
        description="description"
    )

    real_out = ScalarVariable(
        name="real_out",
        valueReference=11,
        causality='output',
        variability='continuous',
        description="description"
    )

    model_description.modelVariables.append(time)
    model_description.modelVariables.append(real_in)
    model_description.modelVariables.append(real_out)

    model_description.outputs.append(Unknown(variable=real_out))
    model_description.initialUnknowns.append(Unknown(variable=real_out))

    create_fmu(model_description)

if __name__ == "__main__":
    main()


def generate_model_description(n_parameters: int = 10, n_inputs: int = 10, n_outputs: int = 10, n_states: int = 10) -> ModelDescription:

    model_description = ModelDescription()

    model_description.fmiVersion = "3.0"
    model_description.modelName = 'model'
    model_description.description = f'A test model with {n_parameters} parameters, {n_inputs} inputs, {n_outputs} outputs, and {n_states} states.'
    model_description.generationTool = f"FMPy {fmpy.__version__}"
    model_description.generationDateAndTime = datetime.now(timezone.utc).isoformat()
    model_description.instantiationToken = str(uuid.uuid4())

    model_description.coSimulation = CoSimulation(
        modelIdentifier="model"
    )

    model_description.defaultExperiment = DefaultExperiment(
        startTime="0.0",
        stopTime="1.0",
        stepSize="1e-3"
    )

    time = ScalarVariable(
        name="time",
        valueReference=0,
        type='Float64',
        causality='independent',
        variability='continuous',
        description="description"
    )

    model_description.modelVariables.append(time)

    vr = 1

    for i in range(n_parameters):
        variable = ScalarVariable(
            name=f"p{i}",
            valueReference=vr,
            type='Float64',
            start='0',
            causality='parameter',
            variability='fixed',
            description=f"Parameter {i}"
        )
        vr += 1
        model_description.modelVariables.append(variable)

    for i in range(n_inputs):
        variable = ModelVariable(
            name=f"u{i}",
            valueReference=vr,
            type='Float64',
            start='0',
            causality='input',
            variability='continuous',
            description=f"Input {i}"
        )
        vr += 1
        model_description.modelVariables.append(variable)

    for i in range(n_outputs):
        variable = ModelVariable(
            name=f"y{i}",
            valueReference=vr,
            type='Float64',
            causality='output',
            variability='continuous',
            description=f"Output {i}"
        )
        vr += 1
        model_description.modelVariables.append(variable)

        model_description.outputs.append(Unknown(variable=variable))
        model_description.initialUnknowns.append(Unknown(variable=variable))

    for i in range(n_outputs):
        variable = ModelVariable(
            name=f"x{i}",
            valueReference=vr,
            type='Float64',
            causality='local',
            variability='continuous',
            description=f"State {i}"
        )
        vr += 1
        model_description.modelVariables.append(variable)

    return model_description
