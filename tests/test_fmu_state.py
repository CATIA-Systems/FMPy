import pytest
import shutil
from fmpy import *


@pytest.mark.parametrize('fmi_version', ['1.0', '2.0', '3.0'])
@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_continue_simulation(reference_fmus_dist_dir, fmi_version):

    pause_time = 0.6
    stop_time = 1.0

    def pause_simulation(time, recorder):

        nonlocal pause_time

        if time >= pause_time:
            pause_time = time
            return False

        return True

    if fmi_version == '1.0':
        filename = reference_fmus_dist_dir / fmi_version / 'cs' / 'BouncingBall.fmu'
    else:
        filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    unzipdir = extract(filename)
    model_description = read_model_description(unzipdir)

    fmu_instance = instantiate_fmu(unzipdir=unzipdir, model_description=model_description)

    # simulate to pause_time
    result1 = simulate_fmu(filename=unzipdir, model_description=model_description, fmu_instance=fmu_instance,
                           stop_time=stop_time, step_finished=pause_simulation, terminate=False)

    # continue the simulation
    result2 = simulate_fmu(filename=unzipdir, model_description=model_description, fmu_instance=fmu_instance,
                           start_time=pause_time, stop_time=stop_time, initialize=False)

    fmu_instance.freeInstance()

    shutil.rmtree(unzipdir, ignore_errors=True)

    assert result1[-1] == result2[0]


@pytest.mark.parametrize('fmi_version', ['2.0', '3.0'])
@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_set_fmu_state(reference_fmus_dist_dir, fmi_version):

    pause_time = 0.6
    stop_time = 1.0
    fmu_state = None

    def get_fmu_state(time, recorder):

        nonlocal pause_time, fmu_state

        if time >= pause_time:
            fmu = recorder.fmu
            fmu_state = fmu.getFMUState()
            pause_time = time
            return False

        return True

    filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    unzipdir = extract(filename)
    model_description = read_model_description(unzipdir)

    fmu_instance = instantiate_fmu(unzipdir=unzipdir, model_description=model_description, fmi_call_logger=print)

    # simulate to pause_time
    result1 = simulate_fmu(filename=unzipdir, model_description=model_description, fmu_instance=fmu_instance,
                           stop_time=stop_time, step_finished=get_fmu_state)

    # continue simulation with the FMU state
    result2 = simulate_fmu(filename=unzipdir, model_description=model_description, fmu_instance=fmu_instance,
                           start_time=pause_time, stop_time=stop_time, fmu_state=fmu_state)

    fmu_instance.freeInstance()

    shutil.rmtree(unzipdir, ignore_errors=True)

    assert result1[-1] == result2[0]


@pytest.mark.parametrize('fmi_version', ['2.0', '3.0'])
@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_serialize_fmu_state(reference_fmus_dist_dir, fmi_version):

    serialization_time = 0.6
    serialized_state = None

    def save_state(time, recorder):
        """ callback to serialize the FMU state and stop the simulation """

        nonlocal serialization_time, serialized_state

        if time >= serialization_time:  # condition to serialize the FMU state
            fmu = recorder.fmu
            serialization_time = time
            state = fmu.getFMUState()
            serialized_state = fmu.serializeFMUState(state)
            return False  # stop the simulation

        return True  # continue the simulation

    filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    # simulate to serialization_time
    result1 = simulate_fmu(filename, stop_time=1.0, step_finished=save_state, fmi_call_logger=print)

    # continue simulation with the serialized state
    result2 = simulate_fmu(filename, start_time=serialization_time, stop_time=1.0, fmu_state=serialized_state, fmi_call_logger=print)

    assert result1[-1] == result2[0]
