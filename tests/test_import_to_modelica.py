import os
from pathlib import Path

import numpy as np
import pytest
from OMPython import ModelicaSystem

from fmpy import simulate_fmu, read_model_description
from fmpy.modelica import generate_examples
from fmpy.util import validate_signal, plot_result
from pymola import Dsres


def pymola_available():
    try:
        import pymola
        return True
    except:
        return False


def om_available():

    try:
        import OMPython
    except:
        return False

    return 'OPENMODELICAHOME' in os.environ


def test_import_fmu_to_modelica(root_dir, reference_fmus_dist_dir):

    generate_examples()


# @pytest.mark.skipif(not om_available(), reason="OpenModelica was not found")
# def test_run_examples_in_om(reference_fmus_dist_dir):
#
#     import os
#     from OMPython import OMCSessionZMQ
#
#     os.environ['OPENMODELICAHOME'] = r'E:\OpenModelica'
#
#     omc = OMCSessionZMQ()
#
#     assert omc.sendExpression('loadFile("E:/Development/FMPy/fmpy/modelica/FMI/package.mo")')
#
#     for fmi_version in [2, 3]:
#         for interface_type in ['CoSimulation', 'ModelExchange']:
#             for model, start_values, stop_time in [
#                 ('BouncingBall', {'e': 0.8}, 3),
#                 ('Dahlquist', {}, 10),
#                 ('Stair', {}, 8),
#                 ('Resource', {}, 1),
#                 ('VanDerPol', {'mu': 2.5}, 20),
#                 # ('Feedthrough', {}, None),
#             ]:
#
#                 info = omc.sendExpression(f'simulate(FMI.Examples.FMI{fmi_version}.{interface_type}.{model}, stopTime={stop_time})')
#
#                 result = Dsres(info['resultFile'])
#
#                 filename = str(reference_fmus_dist_dir / f'{fmi_version}.0' / f'{model}.fmu')
#
#                 model_description = read_model_description(filename)
#
#                 outputs = [v.name for v in model_description.modelVariables if v.causality == 'output']
#
#                 reference = simulate_fmu(filename=filename,
#                                          # start_values=start_values,
#                                          output=outputs, stop_time=stop_time,
#                                          fmi_type=interface_type)
#
#                 for name in outputs:
#                     _, _, _, i_out = validate_signal(result['time'], result[f"'{name}'"], reference['time'],  reference[name])
#                     assert not i_out.any()


@pytest.mark.skipif(not pymola_available(), reason="Pymola was not found")
def test_run_examples_in_dymola(dymola, root_dir, reference_fmus_dist_dir):

    dymola.loadClass(root_dir / 'fmpy' / 'modelica' / 'FMI' / 'package.mo')

    for fmi_version in [2, 3]:
        for interface_type in ['CoSimulation', 'ModelExchange']:
            for model, start_values, stop_time in [
                ('BouncingBall', {'e': 0.8}, None),
                ('Dahlquist', {}, None),
                ('Stair', {}, 8),
                ('Resource', {}, None),
                ('VanDerPol', {'mu': 2.5}, None),
                # ('Feedthrough', {}, None),
            ]:

                filename = str(reference_fmus_dist_dir / f'{fmi_version}.0' / f'{model}.fmu')

                model_description = read_model_description(filename)

                outputs = [v.name for v in model_description.modelVariables if v.causality == 'output']

                reference = simulate_fmu(filename=filename, start_values=start_values, output=outputs, stop_time=stop_time, fmi_type=interface_type)

                intial_values = dict(map(lambda i: (f"'{i[0]}'", i[1]), start_values.items()))

                result = dymola.simulate(
                    model=f'FMI.Examples.FMI{fmi_version}.{interface_type}.{model}',
                    initialValues=intial_values,
                    stopTime=stop_time
                )

                for name in outputs:
                    _, _, _, i_out = validate_signal(result['Time'], result[f"'{name}'"], reference['time'],  reference[name])
                    assert not i_out.any()

                for name, expected in intial_values.items():
                    actual = result[name]
                    assert np.allclose(actual, expected)
