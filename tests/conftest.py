import pytest
from pathlib import Path

from fmpy import extract
from fmpy.util import download_file


@pytest.fixture(scope='session')
def resources_dir():
    yield Path(__file__).parent / 'resources'


@pytest.fixture(scope='session')
def reference_fmus_dist_dir():

    # yield Path(r'E:\Development\Reference-FMUs\fmus')
    version = '0.0.13'
    checksum = 'ad0f0aa89aea5f818274af085c62c6151f9ca7d2a943cbffe66b7a5c2c204b2e'

    zip_file = download_file(
        url=f'https://github.com/modelica/Reference-FMUs/releases/download/v{version}/Reference-FMUs-{version}.zip',
        checksum=checksum)

    dist_dir = Path(__file__).parent / 'resources' / 'Reference-FMUs-dist'

    extract(filename=zip_file, unzipdir=dist_dir)

    yield dist_dir
