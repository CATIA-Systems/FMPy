from fmpy import read_model_description, simulate_fmu


def test_fmi2_container():
    # read_model_description(r"E:\WS\FMPy\tests\work\modelDescription.xml")
    simulate_fmu(r"E:\WS\FMPy\tests\work", fmi_call_logger=print)
