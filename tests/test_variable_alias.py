from fmpy import read_model_description


def test_variable_alias(reference_fmus_dist_dir):
    """ Read a variable with an alias """

    filename = reference_fmus_dist_dir / '3.0' / 'BouncingBall.fmu'

    model_description = read_model_description(filename)

    h = model_description.modelVariables[1]

    h_ft = h.aliases[0]

    assert h_ft.name == 'h_ft'
    assert h_ft.description == 'Position in feet'
    assert h_ft.displayUnit == 'ft'
