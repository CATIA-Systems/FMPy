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

    binaries_dir = Path(__file__).parent / "binaries"

    for platform_tuple, shared_library in [
        ("aarch64-darwin", "container_fmu.dylib"),
        ("x86_64-darwin", "container_fmu.dylib"),
        ("x86_64-linux", "container_fmu.so"),
        ("x86_64-windows", "container_fmu.dll"),
    ]:
        os.makedirs(unzipdir / "binaries" / platform_tuple)
        shutil.copyfile(
            src=binaries_dir / platform_tuple / shared_library,
            dst=unzipdir / "binaries" / platform_tuple / shared_library,
        )

    shutil.make_archive(
        base_name=str(unzipdir / "Container"), format="zip", root_dir=unzipdir
    )

    os.rename(src=str(unzipdir / "Container.zip"), dst=filename)
