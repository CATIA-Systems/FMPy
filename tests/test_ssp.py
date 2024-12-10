import pytest
import numpy as np
from fmpy import platform
from fmpy.ssp.ssd import read_ssd, read_ssv
from fmpy.ssp.simulation import simulate_ssp
import os


if 'SSP_STANDARD_DEV' not in os.environ:
    pytest.skip(
        reason="Environment variable SSP_STANDARD_DEV must point to the clone of https://github.com/modelica/ssp-standard-dev",
        allow_module_level=True
    )

def ssp_dev_path(*segments):
    return os.path.join(os.environ['SSP_STANDARD_DEV'], *segments)

@pytest.mark.skipif(platform != 'win32', reason="Current platform not supported by this SSP")
def test_simulate_sample_system_with_parameters():

    ssv_filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemParameterValues.ssv')
    parameter_set = read_ssv(ssv_filename)

    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystem.ssp')
    sine = lambda t: np.sin(t * 2 * np.pi)
    result = simulate_ssp(filename, stop_time=1.0, step_size=0.01, parameter_set=parameter_set, input={'In1': sine})

    # check if the input has been applied correctly
    assert np.all(np.abs(result['In1'] - sine(result['time'])) < 0.01)

    # plot_result(result, names=['In1', 'Out1'], window_title=filename)

@pytest.mark.skipif(platform != 'win32', reason="Current platform not supported by this SSP")
def test_simulate_sub_system():

    ssp_filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystem.ssp')
    sine = lambda t: np.sin(t * 2 * np.pi)
    result = simulate_ssp(ssp_filename, stop_time=1.0, step_size=0.01, input={'In1': sine})

    # check if the input has been applied correctly
    assert np.all(np.abs(result['In1'] - sine(result['time'])) < 0.01)

    # plot_result(result, names=['In1', 'Out1'], window_title=ssp_filename)

def test_read_ssd_with_referenced_signal_dictionary():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemDictionary.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Dictionary'
    assert 1 == len(ssd.system.elements[2].elements[0].parameterBindings)

def test_read_ssd_with_inlined_signal_dictionary():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemDictionaryInline.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Dictionary all inline'

def test_SampleSystem():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystem.ssp')
    ssd = read_ssd(filename)
    assert 'Simple Sample System' == ssd.name

    # System
    assert 'SampleSystem' == ssd.system.name
    assert 'Very simple Sample System' == ssd.system.description

def test_SampleSystemSubSystem():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystem.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem'

def test_SampleSystemSubSystemDictionary():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemDictionary.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Dictionary'

    # parameter bindings from .ssv file
    parameter_binding = ssd.system.parameterBindings[0]
    assert 'SubSystem.' == parameter_binding.prefix
    assert 'application/x-ssp-parameter-set' == parameter_binding.type

    p1, p2, p3 = parameter_binding.parameterValues[0].parameters
    assert ('FirstFMUInstance1.Gain_Gain', 'Real', '8.0') == (p1.name, p1.type, p1.value)
    assert ('FirstFMUInstance2.Gain_Gain', 'Real', '3.0') == (p2.name, p2.type, p2.value)
    assert ('FirstFMUInstance2.Gain1_Gain', 'Real', '18.0') == (p3.name, p3.type, p3.value)

    # signal dictionary from .ssb file
    signal_dictionary = ssd.system.signalDictionaries[0]
    assert 'MyDictionary' == signal_dictionary.name
    assert 'resources/SampleSignalDictionary.ssb' == signal_dictionary.source
    assert 'application/x-ssp-signal-dictionary' == signal_dictionary.type

    sd_entry1, sd_entry2 = signal_dictionary.entries
    assert ('Var2', 'Real', 'km/h') == (sd_entry1.name, sd_entry1.type, sd_entry1.unit)
    assert ('Var4', 'Real', 'km/h') == (sd_entry2.name, sd_entry2.type, sd_entry2.unit)

    # units
    u1, u2 = ssd.units
    assert ('km/h', 1, -1, 0.2777777777777778) == (u1.name, u1.m, u1.s, u1.factor)
    assert ('m/s', 1, -1) == (u2.name, u2.m, u1.s)

def test_SampleSystemSubSystemDictionaryInline():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemDictionaryInline.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Dictionary all inline'

    # inline parameter bindings
    parameter_binding = ssd.system.parameterBindings[0]
    assert 'SubSystem.' == parameter_binding.prefix
    assert 'application/x-ssp-parameter-set' == parameter_binding.type

    p1, p2, p3 = parameter_binding.parameterValues[0].parameters
    assert ('FirstFMUInstance1.Gain_Gain', 'Real', '8.0') == (p1.name, p1.type, p1.value)
    assert ('FirstFMUInstance2.Gain_Gain', 'Real', '3.0') == (p2.name, p2.type, p2.value)
    assert ('FirstFMUInstance2.Gain1_Gain', 'Real', '18.0') == (p3.name, p3.type, p3.value)

    # inline signal dictionary
    signal_dictionary = ssd.system.signalDictionaries[0]
    assert 'MyDictionary' == signal_dictionary.name
    assert 'application/x-ssp-signal-dictionary' == signal_dictionary.type

    sd_entry1, sd_entry2 = signal_dictionary.entries
    assert ('Var2', 'Real', 'km/h') == (sd_entry1.name, sd_entry1.type, sd_entry1.unit)
    assert ('Var4', 'Real', 'km/h') == (sd_entry2.name, sd_entry2.type, sd_entry2.unit)

def test_SampleSystemSubSystemParamConnectors():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemParamConnectors.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Dictionary all inline, and parameter connectors'

def test_SampleSystemSubSystemReuse():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemReuse.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and Reuse'

def test_SampleSystemSubSystemReuseNested():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemSubSystemReuseNested.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple System with SubSystem and External Reuse'

def test_SampleSystemVariants():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleSystemVariants.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Simple Sample System'

def test_SubSystem():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SubSystem.ssp')
    ssd = read_ssd(filename)
    assert ssd.name == 'Subsystem for External Reuse'

def test_read_ssv():
    filename = ssp_dev_path('SystemStructureDescription', 'examples', 'SampleParameterValues.ssv')
    parameter_set = read_ssv(filename)
    assert 6 == len(parameter_set.parameters)

def test_ControlledDrivetrain():
    ssp_filename = ssp_dev_path('Examples', 'ControlledDrivetrain', 'ControlledDrivetrain.ssp')
    result = simulate_ssp(ssp_filename, step_size=1e-2, stop_time=4.0)
    # plot_result(result)
