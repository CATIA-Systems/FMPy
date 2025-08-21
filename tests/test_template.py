from tempfile import TemporaryDirectory

from fmpy import simulate_fmu, extract
from fmpy.build import build_platform_binary
from fmpy.template import create_fmu, generate_model_description
import numpy as np

from fmpy.util import create_zip_archive


def test_create_fmu(work_dir):

    model_description = generate_model_description()

    filename = work_dir / 'Model.fmu'

    create_fmu(model_description, filename)

    with TemporaryDirectory() as tempdir:
        extract(filename, tempdir)
        build_platform_binary(tempdir)
        create_zip_archive(filename, tempdir)

    result = simulate_fmu(filename, start_values={'u5': 5}, output=['u5'])

    assert np.all(result['u5'] == 5)
