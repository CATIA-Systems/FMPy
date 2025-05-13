import os
from os import makedirs
from shutil import rmtree

import pytest
from pathlib import Path

from fmpy import extract
from fmpy.util import download_file


def pytest_addoption(parser):
    parser.addoption('--executable', default=None, help="Dymola executable to connect to")


@pytest.fixture(scope='session')
def root_dir():
    yield Path(__file__).parent.parent


@pytest.fixture(scope='session')
def work_dir():
    path = Path(__file__).parent / 'work'
    if not path.exists():
        os.makedirs(path)
    yield path


@pytest.fixture(scope='session')
def resources_dir():
    yield Path(__file__).parent / 'resources'


@pytest.fixture(scope='session')
def reference_fmus_dist_dir(resources_dir) -> Path:

    version = '0.0.37'
    checksum = '9b0d6bfbceef6fc0e724620ea748f26d03ca3cf6048d17436c49b9340d553ec4'

    zip_file = download_file(
        url=f'https://github.com/modelica/Reference-FMUs/releases/download/v{version}/Reference-FMUs-{version}.zip',
        checksum=checksum)

    dist_dir = resources_dir / 'Reference-FMUs-dist'

    extract(filename=zip_file, unzipdir=dist_dir)

    yield dist_dir


@pytest.fixture(scope='session')
def reference_fmus_repo_dir(resources_dir):
    yield Path(__file__).absolute().parent.parent / 'native' / 'thirdparty' / 'Reference-FMUs'


@pytest.fixture(scope='session')
def executable(request):

    from pymola import findDymolaExecutables

    executable = request.config.getoption('--executable')

    if executable is None:
        executables = findDymolaExecutables()
        executable = executables[-1]

    yield executable


@pytest.fixture(scope='module')
def dymola(executable, work_dir):

    from pymola import Dymola

    if work_dir.exists():
        rmtree(work_dir)

    makedirs(work_dir)

    with Dymola(executable=executable, showWindow=True, debug=False) as dymola:
        dymola.cd(work_dir)

        # ensure, that MSL is loaded, as functions like exportSSP do not trigger demand loading
        dymola.openModelFile('Modelica')

        # build 64-bit binaries
        dymola.setVariable('Advanced.CompileWith64', 2)

        yield dymola
