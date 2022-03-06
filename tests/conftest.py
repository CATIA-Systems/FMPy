import pytest
from pathlib import Path

from fmpy import extract
from fmpy.util import download_file


@pytest.fixture(scope='session')
def resources_dir():
    yield Path(__file__).parent / 'resources'


@pytest.fixture(scope='session')
def reference_fmus_dist_dir(resources_dir):

    version = '0.0.14'
    checksum = 'a4a4916702d2bb6b300da9120ecfa62f5091c8a53926b0afe1f04b1933e04f03'

    zip_file = download_file(
        url=f'https://github.com/modelica/Reference-FMUs/releases/download/v{version}/Reference-FMUs-{version}.zip',
        checksum=checksum)

    dist_dir = resources_dir / 'Reference-FMUs-dist'

    extract(filename=zip_file, unzipdir=dist_dir)

    yield dist_dir


@pytest.fixture(scope='session')
def reference_fmus_repo_dir(resources_dir):

    version = '0.0.14'
    checksum = '93ffb56774b15130b6993d345dff1795ddce7872706c0b4d8f4d8edd361a8a7a'

    zip_file = download_file(
        url=f'https://github.com/modelica/Reference-FMUs/archive/v{version}.zip',
        checksum=checksum)

    extract(filename=zip_file, unzipdir=resources_dir)

    repo_dir = resources_dir / f'Reference-FMUs-{version}'

    yield repo_dir
