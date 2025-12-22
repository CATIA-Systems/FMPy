import os
import shutil
import zipfile
from pathlib import Path


from container_fmu import write_model_description, Configuration, write_configuration


def create_container_fmu(config: Configuration, unzipdir: Path, filename: Path) -> None:
    shutil.rmtree(unzipdir)
    os.makedirs(unzipdir)

    for component in config.components:
        fmu_path = Path(component.filename)
        with zipfile.ZipFile(fmu_path, "r") as zip_file:
            zip_file.extractall(unzipdir / "resources" / fmu_path.stem)

    write_model_description(config, unzipdir / "modelDescription.xml")

    write_configuration(config, unzipdir / "resources" / "container.json")

    os.makedirs(unzipdir / "binaries" / "x86_64-windows")

    shutil.copyfile(
        src=r"E:\WS\ContainerFMU\container\target\debug\container.dll",  # template_dir / "binaries" / "x86_64-windows" / "container.dll",
        dst=unzipdir / "binaries" / "x86_64-windows" / "container.dll",
    )

    shutil.make_archive(
        base_name=str(unzipdir / "Container"), format="zip", root_dir=unzipdir
    )

    os.rename(src=str(unzipdir / "Container.zip"), dst=filename)
