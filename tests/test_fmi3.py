import unittest
from unittest import skipIf
import numpy as np
import os
from fmpy import read_model_description
from fmpy.fmi3 import *
from ctypes import cast, POINTER


@skipIf('FMI3_FMUS_DIR' not in os.environ, "Environment variable FMI3_FMUS_DIR is required for this test")
class FMI3Test(unittest.TestCase):

    def test_read_model_description(self):

        unzipdir = os.path.join(os.environ['FMI3_FMUS_DIR'], 'linearOperatorcs30')

        model_description = read_model_description(unzipdir)

        fmu = FMU3Slave(
            guid=model_description.guid,
            unzipDirectory=unzipdir,
            modelIdentifier=model_description.coSimulation.modelIdentifier
        )

        fmu.instantiate()
        fmu.setupExperiment()
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        variables = dict((v.name, v) for v in model_description.modelVariables)

        def get_real(variable):
            vr = (fmi3ValueReference * 1)(variable.valueReference)
            value = np.zeros(variable.extent)
            status = fmu.fmi3GetReal(fmu.component, vr, len(vr), cast(value.ctypes.data, POINTER(fmi3Float64)), value.size)
            self.assertEqual(status, fmi3OK)
            return value

        def set_real(variable, data):
            vr = (fmi3ValueReference * 1)(variable.valueReference)
            status = fmu.fmi3SetReal(fmu.component, vr, len(vr), cast(data.ctypes.data, POINTER(fmi3Float64)), data.size)
            self.assertEqual(status, fmi3OK)

        # get "in"
        in_data = get_real(variables['in'])
        self.assertTrue(np.all(in_data == [1, 1, 1]))

        # get "operator"
        operator_data = get_real(variables['operator'])
        self.assertTrue(np.all(operator_data.flat == [1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 1]))

        # set "in"
        in_data[:] = [1, 2, 3]
        set_real(variables['in'], in_data)

        # get "out"
        out_data = get_real(variables['out'])
        self.assertTrue(np.all(out_data == [1, 2, 3, 6]))

        # clean up
        fmu.terminate()
        fmu.freeInstance()
        # fmu.freeLibrary()
