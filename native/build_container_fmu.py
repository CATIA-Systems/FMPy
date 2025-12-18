from platform import system

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

if os.name == 'nt':
    shared_library_src_name = f"container_fmu{sharedLibraryExtension}"
else:
    shared_library_src_name = f"libcontainer_fmu{sharedLibraryExtension}"

shared_library_dst_name = f"container_fmu{sharedLibraryExtension}"

# build Container FMU
if system() == "Darwin":
    check_call(["cargo", "build", "--target", "x86_64-apple-darwin", "--release"], cwd=native / "container-fmu")

    check_call(["find", "."], cwd=native / "container-fmu")

    shutil.copy(
        src=native / "container-fmu" / "target" / "x86_64-apple-darwin" / "release" / shared_library_src_name,
        dst=native.parent / "src" / "fmpy" / "container_fmu" / "x86_64-darwin" / shared_library_dst_name
    )

    check_call(["cargo", "build", "--target", "aarch64-apple-darwin", "--release"], cwd=native / "container-fmu")

    check_call(["find", "."], cwd=native / "container-fmu")

    shutil.copy(
        src=native / "container-fmu" / "target" / "aarch64-apple-darwin" / "release" / shared_library_src_name,
        dst=native.parent / "src" / "fmpy" / "container_fmu" / "aarch64-darwin" / shared_library_dst_name
    )

    # check_call(["cargo", "test", "--release"], cwd=native / "container-fmu")
else:
    check_call(["cargo", "build", "--release"], cwd=native / "container-fmu")

    shutil.copy(
        src=native / "container-fmu" / "target" / "release" / shared_library_src_name,
        dst=native.parent / "src" / "fmpy" / "container_fmu" / platform_tuple / shared_library_dst_name
    )

    check_call(["cargo", "test", "--release"], cwd=native / "container-fmu")
