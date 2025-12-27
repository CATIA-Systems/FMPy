import os
import shutil
import zipfile
from pathlib import Path


from fmpy.container_fmu import Configuration, write_configuration
from fmpy.model_description import write_model_description, CoSimulation


def create_container_fmu(config: Configuration, unzipdir: Path, filename: Path) -> None:

    shutil.rmtree(unzipdir)
    os.makedirs(unzipdir)

    # extract nested FMUs to resources/
    for component in config.components:
        fmu_path = Path(component.filename)
        with zipfile.ZipFile(fmu_path, "r") as zip_file:
            zip_file.extractall(unzipdir / "resources" / fmu_path.stem)

    # augment the model description
    config.modelDescription.coSimulation.modelIdentifier="container_fmu"

    for i, variable in enumerate(config.modelDescription.modelVariables):
        variable.valueReference = i

    # write the modelDescription.xml
    write_model_description(config.modelDescription, unzipdir / "modelDescription.xml")

    write_configuration(config, unzipdir / "resources" / "container.json")

    os.makedirs(unzipdir / "binaries" / "x86_64-windows")

    binaries_dir = Path(__file__).parent / "binaries"

    shutil.copyfile(
        src=binaries_dir / "x86_64-windows" / "container_fmu.dll",
        dst=unzipdir / "binaries" / "x86_64-windows" / "container_fmu.dll",
    )

    shutil.make_archive(
        base_name=str(unzipdir / "Container"), format="zip", root_dir=unzipdir
    )

    os.rename(src=str(unzipdir / "Container.zip"), dst=filename)
