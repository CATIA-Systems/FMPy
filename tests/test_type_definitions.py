import unittest
from fmpy import read_model_description
from fmpy.util import download_file


class TypeDefinitionsTest(unittest.TestCase):

    def test_type_definitions(self):
        """ Read the Type Definitions from the modelDescription.xml """

        for fmi_version in ['1.0', '2.0']:

            download_file('https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_'
                          + fmi_version + '/CoSimulation/win64/Dymola/2017/DFFREG/DFFREG.fmu')

            model_description = read_model_description('DFFREG.fmu')

            real = model_description.typeDefinitions[0]

            self.assertEqual('Real', real.type)
            self.assertEqual('Modelica.SIunits.Time', real.name)
            self.assertEqual('Time', real.quantity)
            self.assertEqual('s', real.unit)

            logic = model_description.typeDefinitions[1]

            self.assertEqual('Enumeration', logic.type)
            self.assertEqual('Modelica.Electrical.Digital.Interfaces.Logic', logic.name)
            self.assertEqual(9, len(logic.items))

            high_impedance = logic.items[4]

            self.assertEqual("'Z'", high_impedance.name)
            self.assertEqual(5, int(high_impedance.value))
            self.assertEqual("Z  High Impedance", high_impedance.description)


if __name__ == '__main__':
    unittest.main()
