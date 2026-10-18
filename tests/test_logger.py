import gc
import pytest
from fmpy import extract, read_model_description, instantiate_fmu, platform_tuple
from fmpy.fmi1 import FMICallException


def reference_fmu(reference_fmus_dist_dir, fmi_version):

    if fmi_version == '1.0':
        filename = reference_fmus_dist_dir / fmi_version / 'cs' / 'BouncingBall.fmu'
    else:
        filename = reference_fmus_dist_dir / fmi_version / 'BouncingBall.fmu'

    unzipdir = extract(filename)
    model_description = read_model_description(unzipdir)

    return unzipdir, model_description


def log_error(fmu):
    """ Make the FMU log an error by calling getReal() with an invalid value reference """

    with pytest.raises(FMICallException):
        fmu.getReal([12345])


@pytest.mark.parametrize('fmi_version', ['1.0', '2.0'])
@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_default_logger_after_custom_logger(reference_fmus_dist_dir, fmi_version, capsys):
    """ https://github.com/CATIA-Systems/FMPy/issues/899 """

    unzipdir, model_description = reference_fmu(reference_fmus_dist_dir, fmi_version)

    messages = []

    def logger(component, instanceName, status, category, message):
        messages.append(message.decode('utf-8'))

    fmu = instantiate_fmu(unzipdir, model_description, fmi_type='CoSimulation', logger=logger)
    log_error(fmu)
    fmu.freeInstance()

    assert len(messages) > 0

    # free the callbacks of the custom logger
    del fmu
    gc.collect()

    capsys.readouterr()

    fmu = instantiate_fmu(unzipdir, model_description, fmi_type='CoSimulation')
    log_error(fmu)  # used to crash
    fmu.freeInstance()

    assert '[ERROR]' in capsys.readouterr().out


@pytest.mark.skipif(platform_tuple == "aarch64-darwin", reason="Not supported on aarch64-darwin")
def test_loggers_of_simultaneous_instances(reference_fmus_dist_dir):

    unzipdir, model_description = reference_fmu(reference_fmus_dist_dir, '2.0')

    messages1 = []
    messages2 = []

    fmu1 = instantiate_fmu(unzipdir, model_description, fmi_type='CoSimulation', logger=lambda *args: messages1.append(args))
    fmu2 = instantiate_fmu(unzipdir, model_description, fmi_type='CoSimulation', logger=lambda *args: messages2.append(args))

    log_error(fmu1)

    assert len(messages1) > 0
    assert len(messages2) == 0

    log_error(fmu2)

    assert len(messages2) == len(messages1)

    # the original componentEnvironment is passed to the logger
    assert messages1[0][0] is None

    fmu1.freeInstance()
    fmu2.freeInstance()
