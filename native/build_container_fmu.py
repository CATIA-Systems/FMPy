import os

from subprocess import check_call
from fmpy import sharedLibraryExtension, platform, platform_tuple

import shutil

from pathlib import Path

from fmpy import extract
from fmpy.util import download_file

# download test resources
zip_file = download_file(
    url="https://github.com/modelica/Reference-FMUs/releases/download/v0.0.39/Reference-FMUs-0.0.39.zip",
    checksum="6863d55e5818e1ca4e4614c4d4ba4047a921b4495f6336e7002874ed791f6c2a"
)

unzipdir = extract(zip_file)

path = Path(unzipdir)
native = Path(__file__).parent

extract(filename=path / "2.0" / "Feedthrough.fmu",
        unzipdir=native / "container-fmu" / "fmi" / "tests" / "resources" / "fmi2" / "Feedthrough")

extract(filename=path / "3.0" / "Feedthrough.fmu",
        unzipdir=native / "container-fmu" / "fmi" / "tests" / "resources" / "fmi3" / "Feedthrough")

extract(filename=path / "2.0" / "Feedthrough.fmu",
        unzipdir=native / "container-fmu" / "container-fmu" / "tests" / "resources" / "fmi2" / "resources" / "Feedthrough")

extract(filename=path / "3.0" / "Feedthrough.fmu",
        unzipdir=native / "container-fmu" / "container-fmu" / "tests" / "resources" / "fmi3" / "resources" / "Feedthrough")

shutil.rmtree(unzipdir)

# build Container FMU
check_call(["cargo", "build", "--release"], cwd=native / "container-fmu")
check_call(["cargo", "test", "--release"], cwd=native / "container-fmu")

if os.name == 'nt':
    shared_library_prefix = ""
else:
    shared_library_prefix = "lib"

shutil.copy(
    src=native / "container-fmu" / "target" / "release" / f"{shared_library_prefix}container_fmu{sharedLibraryExtension}",
    dst=native.parent / "src" / "fmpy" / "container_fmu" / platform_tuple / f"container{sharedLibraryExtension}"
)
