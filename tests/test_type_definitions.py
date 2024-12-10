from fmpy import read_model_description
from fmpy.util import download_file


def test_type_definitions():
    """ Read the Type Definitions from the modelDescription.xml """

    for fmi_version in ['1.0', '2.0']:

        filename = download_file('https://github.com/modelica/fmi-cross-check/raw/master/fmus/'
                      + fmi_version + '/cs/win64/Dymola/2017/DFFREG/DFFREG.fmu')

        model_description = read_model_description(filename)

        real = model_description.typeDefinitions[0]

        assert 'Real' == real.type
        assert 'Modelica.SIunits.Time' == real.name
        assert 'Time' == real.quantity
        assert 's' == real.unit

        logic = model_description.typeDefinitions[1]

        assert 'Enumeration' == logic.type
        assert 'Modelica.Electrical.Digital.Interfaces.Logic' == logic.name
        assert 9 == len(logic.items)

        high_impedance = logic.items[4]

        assert "'Z'" == high_impedance.name
        assert 5 == int(high_impedance.value)
        assert "Z  High Impedance" == high_impedance.description
