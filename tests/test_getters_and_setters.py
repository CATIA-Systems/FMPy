import unittest
from fmpy import platform, read_model_description, extract
from fmpy.fmi1 import FMU1Slave
from fmpy.fmi2 import FMU2Slave
from fmpy.util import download_test_file
import shutil


class GettersAndSettersTest(unittest.TestCase):

    def test_getters_and_setters(self):

        if platform.startswith('win'):
            fmi_versions = ['1.0', '2.0']
        else:
            return

        for fmi_version in fmi_versions:

            model_name = 'BooleanNetwork1'
            filename = model_name + '.fmu'

            download_test_file(fmi_version, 'CoSimulation', 'Dymola', '2017', model_name, filename)

            modelDescription = read_model_description(filename)
            unzipdir = extract(filename)

            guid = modelDescription.guid
            modelIdentifier = modelDescription.coSimulation.modelIdentifier

            variables = {}

            for v in modelDescription.modelVariables:
                variables[v.name] = v

            args = {'guid': guid,
                    'modelIdentifier': modelIdentifier,
                    'unzipDirectory': unzipdir,
                    'instanceName': None}

            if fmi_version == '1.0':
                fmu = FMU1Slave(**args)
                fmu.instantiate("instance1")
                fmu.initialize()
            else:
                fmu = FMU2Slave(**args)
                fmu.instantiate(loggingOn=False)
                fmu.setupExperiment(tolerance=None)
                fmu.enterInitializationMode()
                fmu.exitInitializationMode()

            # set and get Real
            vr = [variables['booleanPulse1.width'].valueReference]
            value = [30.0]
            fmu.setReal(vr, value)
            result = fmu.getReal(vr)
            self.assertTrue(result[0] == value[0])

            # set and get Integer
            vr = [variables['integerConstant.k'].valueReference]
            value = [-4]
            fmu.setInteger(vr, value)
            result = fmu.getInteger(vr)
            self.assertTrue(result[0] == value[0])

            # set and get Boolean
            vr = [variables['rSFlipFlop.Qini'].valueReference]
            value = [True]
            fmu.setBoolean(vr, value)
            result = fmu.getBoolean(vr)
            self.assertTrue(result[0] == value[0])

            # TODO: set and get String

            # clean up
            fmu.terminate()
            fmu.freeInstance()
            shutil.rmtree(unzipdir)


if __name__ == '__main__':
    unittest.main()
