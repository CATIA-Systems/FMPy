import subprocess

import os
from os import PathLike
from tempfile import TemporaryDirectory

from subprocess import Popen, PIPE

from pathlib import Path

from typing import Sequence

from PySide6.QtCore import QThread, Signal, QObject, QDateTime
from typing_extensions import override

from fmpy.build import Generator, Platform, Configuration, create_cmake_settings, wsl_path


class BuildThread(QThread):

    messageChanged = Signal(str, str)

    def __init__(
            self,
            unzipdir: PathLike,
            build_dir: PathLike | None,
            generator: Generator | None = None,
            platform: Platform | None = None,
            configuration: Configuration = "Release",
            with_wsl: bool = False,
            all_warnings: bool = False,
            warning_as_error: bool = False,
            parent: QObject | None = None
    ):
            super().__init__(parent=parent)
            self.unzipdir = Path(unzipdir).absolute()
            self.build_dir = build_dir
            self.generator = generator
            self.platform = platform
            self.configuration = configuration
            self.with_wsl = with_wsl
            self.all_warnings = all_warnings
            self.warning_as_error = warning_as_error

    @override
    def run(self) -> None:

        start_time = QDateTime.currentMSecsSinceEpoch()

        try:
            if self.build_dir:
                self.build_dir = Path(self.build_dir).absolute()
            else:
                temp_dir = TemporaryDirectory()
                self.build_dir = Path(temp_dir.name).absolute()

            cmake_options = {
                "CMAKE_COMPILE_WARNING_AS_ERROR:BOOL": "ON" if self.warning_as_error else "OFF"
            }

            create_cmake_settings(
                unzipdir=self.unzipdir,
                build_dir=self.build_dir,
                generator=self.generator,
                platform=self.platform,
                configuration=self.configuration,
                all_warnings=self.all_warnings,
                with_wsl=self.with_wsl,
                cmake_options=cmake_options
            )

            source_dir = Path(__file__).parent.parent / "c-code"

            if self.with_wsl:
                source_dir = wsl_path(source_dir)
                build_dir = wsl_path(self.build_dir)
                program = ["wsl", "cmake"]
            else:
                source_dir = source_dir.as_posix()
                build_dir =self.build_dir.absolute().as_posix()
                program = ["cmake"]

            if self.run_command(program + ["-S", source_dir, "-B", build_dir]) != 0:
                self.messageChanged.emit("error", "Failed to generate CMake project.")
                return

            if self.run_command(program + ["--build", build_dir, "--target", "install", "--config", self.configuration]) != 0:
                self.messageChanged.emit("error", "Failed to build CMake project.")
                return

        except Exception as ex:
            self.messageChanged.emit("error", str(ex))
            self.messageChanged.emit("error", "Failed to build platform binary.")

        stop_time = QDateTime.currentMSecsSinceEpoch()
        elapsed_time = ((stop_time - start_time) / 1000.)

        self.messageChanged.emit("info", f"Building platform binary took {elapsed_time} s.")

    def run_command(self, command: Sequence[str]) -> int:

        self.messageChanged.emit("debug", " ".join(command))

        startupinfo = None

        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        with Popen(command, stdout=PIPE, stderr=PIPE, bufsize=1, text=True, encoding="utf-8", startupinfo=startupinfo) as process:

            for line in process.stdout:
                self.messageChanged.emit("info", line)

            for line in process.stderr:
                self.messageChanged.emit("error", line)

            process.wait()

            return process.returncode
