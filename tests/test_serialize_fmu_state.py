import unittest
from fmpy import read_model_description, extract
from fmpy.fmi2 import FMU2Slave
from fmpy.util import download_test_file
import shutil


class SerializeFMUStateTest(unittest.TestCase):

    def test_serialize_fmu_state(self):

        fmu_filename = 'Rectifier.fmu'

        # download the FMU
        download_test_file('2.0', 'cs', 'MapleSim', '2016.2', 'Rectifier', fmu_filename)

        # read the model description
        model_description = read_model_description(fmu_filename)

        # extract the FMU
        unzipdir = extract(fmu_filename)

        # instantiate the FMU
        fmu = FMU2Slave(guid=model_description.guid,
                        unzipDirectory=unzipdir,
                        modelIdentifier=model_description.coSimulation.modelIdentifier)

        # initialize
        fmu.instantiate()
        fmu.setupExperiment()
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

        # get the FMU state
        state = fmu.getFMUstate()

        # serialize the FMU state
        serialized_state = fmu.serializeFMUstate(state)

        # de-serialize the FMU state (re-using memory)
        deserialized_state = fmu.deSerializeFMUstate(serialized_state, state)

        # set the FMU state
        fmu.setFMUstate(deserialized_state)

        # free the FMU state
        fmu.freeFMUstate(deserialized_state)

        fmu.terminate()
        fmu.freeInstance()

        # clean up
        shutil.rmtree(unzipdir)
