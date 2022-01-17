import pytest
from pathlib import Path


@pytest.fixture(scope='session')
def resources_dir():
    yield Path(__file__).parent / 'resources'
