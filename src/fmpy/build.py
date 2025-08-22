import subprocess
from os import PathLike
from typing import Literal

from tempfile import TemporaryDirectory

from pathlib import Path

from fmpy import read_model_description
import fmpy


Generator = Literal[
    "Visual Studio 17 2022",
    "Visual Studio 16 2019",
    "Visual Studio 15 2017",
    "Visual Studio 14 2015",
    "MinGW Makefiles",
    "Unix Makefiles",
]

Platform = Literal["ARM", "Win32", "x64"]

Configuration = Literal["Release", "Debug"]


def wsl_path(path: str | PathLike) -> str:
    output = subprocess.check_output(["wsl", "wslpath", "-a", Path(path).as_posix()])
    return output.decode('utf-8').strip()


def create_cmake_settings(
    unzipdir: str | PathLike,
    build_dir: str | PathLike,
    generator: Generator | None = None,
    platform: Platform | None = None,
    configuration: Configuration = "Release",
    all_warnings: bool = False,
    with_wsl: bool = False,
    cmake_options: dict[str,str] | None = None
) -> None:

    unzipdir = Path(unzipdir)

    build_dir = Path(build_dir)

    include_dirs = [(unzipdir / 'sources').as_posix()]

    model_description = read_model_description(unzipdir)

    source_file_set = model_description.buildConfigurations[0].sourceFileSets[0]

    sources = [(unzipdir / "sources" / file).as_posix() for file in source_file_set.sourceFiles]

    definitions = [f"{definition.name}={definition.value}" for definition in source_file_set.preprocessorDefinitions]

    is_fmi2 = model_description.fmiVersion == "2.0"

    if model_description.coSimulation:
        model_identifier = model_description.coSimulation.modelIdentifier
    else:
        model_identifier = model_description.modelExchange.modelIdentifier

    if fmpy.system == "windows":
        if with_wsl:
            include_dirs = map(wsl_path, include_dirs)
            sources = map(wsl_path, sources)
            target_dir = unzipdir / 'binaries' / 'x86_64-linux'
            target_dir = wsl_path(target_dir)
        else:
            if platform == "Win32":
                binary_dir = "win32" if is_fmi2 else "x86-windows"
            else:
                binary_dir = "win64" if is_fmi2 else "x86_64-windows"
            target_dir = (unzipdir / 'binaries' / binary_dir).as_posix()
    else:
        binary_dir = fmpy.platform if is_fmi2 else fmpy.platform_tuple
        target_dir = (unzipdir / 'binaries' / binary_dir).as_posix()

    with open(build_dir / "CMakeCache.txt", "w") as cache:
        if generator:
            cache.write(f"CMAKE_GENERATOR:INTERNAL={generator}\n")
        if platform:
            cache.write(f"CMAKE_GENERATOR_PLATFORM:INTERNAL={platform}\n")
        cache.write(f"CMAKE_BUILD_TYPE:STRING={configuration}\n")
        cache.write(f"FMI_MODEL_IDENTIFIER:STRING={model_identifier}\n")
        cache.write(f"FMI_INCLUDE_DIRS:STRING={';'.join(include_dirs)}\n")
        cache.write(f"FMI_SOURCES:STRING={';'.join(sources)}\n")
        cache.write(f"FMI_DEFINITIONS:STRING={';'.join(definitions)}\n")
        cache.write(f"FMI_TARGET_DIR:STRING={target_dir}\n")
        cache.write(f"FMI_ALL_WARNINGS:BOOL={'ON' if all_warnings else 'OFF'}\n")
        if cmake_options:
            for name, value in cmake_options.items():
                cache.write(f"{name}={value}\n")


def build_platform_binary(
        unzipdir: str | PathLike,
        build_dir: str | PathLike | None = None,
        generator: Generator | None = None,
        platform: Platform | None = None,
        configuration: Configuration = "Release",
        all_warnings: bool = False,
        with_wsl: bool = False,
        cmake_options: dict[str, str] | None = None
) -> None:

    root = Path(__file__).parent
    source_dir = (root / "c-code").as_posix()

    unzipdir = Path(unzipdir)

    if build_dir:
        build_dir = Path(build_dir)
    else:
        temp_dir = TemporaryDirectory()
        build_dir = Path(temp_dir.name)

    create_cmake_settings(unzipdir, build_dir, generator, platform, configuration, all_warnings, with_wsl, cmake_options)

    if with_wsl:
        program = ["wsl", "cmake"]
        build_dir = wsl_path(build_dir)
        source_dir = wsl_path(source_dir)
    else:
        program = ["cmake"]
        build_dir = build_dir.as_posix()

    command = program + [
        "-S", source_dir,
        "-B", build_dir,
    ]

    subprocess.check_call(command)

    command = program + [
        "--build", build_dir,
        "--target", "install",
    ]

    if configuration:
        command += ["--config", configuration]

    subprocess.check_call(command)
