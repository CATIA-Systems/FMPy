from fmpy import simulate_fmu
from fmpy.template import create_fmu, generate_model_description
from fmpy.util import compile_platform_binary
import numpy as np


def test_create_fmu(work_dir):

    model_description = generate_model_description()

    filename = work_dir / 'Model.fmu'

    create_fmu(model_description, filename)

    compile_platform_binary(filename)

    result = simulate_fmu(filename, start_values={'u5': 5}, output=['u5'])

    assert np.all(result['u5'] == 5)
