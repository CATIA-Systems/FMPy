import pytest

from fmpy.util import download_file, validate_result
from fmpy import *


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_fmi1_cs(reference_fmus_dist_dir):
    for model_name in ['BouncingBall', 'Dahlquist', 'Resource', 'Stair', 'VanDerPol']:
        filename = reference_fmus_dist_dir / '1.0' / 'cs' / f'{model_name}.fmu'
        result = simulate_fmu(filename)
        # plot_result(result)


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_fmi1_me(reference_fmus_dist_dir):
    for model_name in ['BouncingBall', 'Dahlquist', 'Stair', 'VanDerPol']:
        filename = reference_fmus_dist_dir / '1.0' / 'me' / f'{model_name}.fmu'
        result = simulate_fmu(filename)
        # plot_result(result)


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_fmi2(reference_fmus_dist_dir):
    for model_name in ['BouncingBall', 'Dahlquist', 'Feedthrough', 'Resource', 'Stair', 'VanDerPol']:
        filename = reference_fmus_dist_dir / '2.0' / f'{model_name}.fmu'
        for fmi_type in ['ModelExchange', 'CoSimulation']:
            result = simulate_fmu(filename, fmi_type=fmi_type)
            # plot_result(result)


def test_fmi3(reference_fmus_dist_dir, reference_fmus_repo_dir):

    for model_name in ['BouncingBall',
                       # 'Dahlquist',  # skip until #659 is fixed
                       'Feedthrough', 'Resource', 'Stair', 'VanDerPol']:

        if model_name == 'Feedthrough':
            start_values = {
                'Float64_fixed_parameter': 1,
                'String_input': "FMI is awesome!"
            }
            output_interval = 1e-3
            in_csv = reference_fmus_repo_dir / model_name / f'{model_name}_in.csv'
            input = read_csv(in_csv) if os.path.isfile(in_csv) else None
        else:
            start_values = {}
            input = None
            output_interval = None

        filename = reference_fmus_dist_dir / '3.0' / f'{model_name}.fmu'

        for fmi_type in ['ModelExchange', 'CoSimulation']:
            simulate_fmu(filename, fmi_type=fmi_type, start_values=start_values, input=input, output_interval=output_interval)


def test_fmi3_clocks(reference_fmus_dist_dir):
    """ Test the SE specific API """

    import shutil

    filename = reference_fmus_dist_dir / '3.0' / f'Clocks.fmu'

    model_description = read_model_description(filename)

    unzipdir = extract(filename)

    fmu = instantiate_fmu(unzipdir, model_description, fmi_type='ScheduledExecution')

    fmu.instantiate()

    fmu.enterInitializationMode()
    fmu.exitInitializationMode()

    fmu.activateModelPartition(clockReference=1001, activationTime=0)

    fmu.terminate()
    fmu.freeInstance()

    shutil.rmtree(unzipdir, ignore_errors=True)
