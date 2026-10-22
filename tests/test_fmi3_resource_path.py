import os
import tempfile
from unittest.mock import MagicMock
from fmpy.fmi3 import FMU3Model, FMU3Slave, FMU3ScheduledExecution


def test_fmi3_instantiate_model_exchange_resource_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        fmu = FMU3Model.__new__(FMU3Model)
        fmu.unzipDirectory = tmpdir
        fmu.instanceName = "inst1"
        fmu.guid = "{guid}"
        fmu.fmi3InstantiateModelExchange = MagicMock(return_value=123)

        # 1. No resources directory -> resourcePath must be None (NULL pointer)
        fmu.instantiate()
        fmu.fmi3InstantiateModelExchange.assert_called_once()
        assert fmu.fmi3InstantiateModelExchange.call_args[0][2] is None

        # 2. Existing resources directory -> resourcePath must be encoded path
        fmu.fmi3InstantiateModelExchange.reset_mock()
        res_dir = os.path.join(tmpdir, "resources")
        os.makedirs(res_dir, exist_ok=True)
        fmu.instantiate()
        fmu.fmi3InstantiateModelExchange.assert_called_once()
        expected = (res_dir + os.path.sep).encode("utf-8")
        assert fmu.fmi3InstantiateModelExchange.call_args[0][2] == expected

        # 3. Explicit resourcePath parameter -> uses provided path
        fmu.fmi3InstantiateModelExchange.reset_mock()
        fmu.instantiate(resourcePath="/custom/res/")
        fmu.fmi3InstantiateModelExchange.assert_called_once()
        assert fmu.fmi3InstantiateModelExchange.call_args[0][2] == b"/custom/res/"


def test_fmi3_instantiate_co_simulation_resource_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        fmu = FMU3Slave.__new__(FMU3Slave)
        fmu.unzipDirectory = tmpdir
        fmu.instanceName = "inst1"
        fmu.guid = "{guid}"
        fmu.fmi3InstantiateCoSimulation = MagicMock(return_value=123)

        # 1. No resources directory -> resourcePath must be None (NULL pointer)
        fmu.instantiate()
        fmu.fmi3InstantiateCoSimulation.assert_called_once()
        assert fmu.fmi3InstantiateCoSimulation.call_args[0][2] is None

        # 2. Existing resources directory -> resourcePath must be encoded path
        fmu.fmi3InstantiateCoSimulation.reset_mock()
        res_dir = os.path.join(tmpdir, "resources")
        os.makedirs(res_dir, exist_ok=True)
        fmu.instantiate()
        fmu.fmi3InstantiateCoSimulation.assert_called_once()
        expected = (res_dir + os.path.sep).encode("utf-8")
        assert fmu.fmi3InstantiateCoSimulation.call_args[0][2] == expected

        # 3. Explicit resourcePath parameter -> uses provided path
        fmu.fmi3InstantiateCoSimulation.reset_mock()
        fmu.instantiate(resourcePath="/custom/res/")
        fmu.fmi3InstantiateCoSimulation.assert_called_once()
        assert fmu.fmi3InstantiateCoSimulation.call_args[0][2] == b"/custom/res/"


def test_fmi3_instantiate_scheduled_execution_resource_path():
    with tempfile.TemporaryDirectory() as tmpdir:
        fmu = FMU3ScheduledExecution.__new__(FMU3ScheduledExecution)
        fmu.unzipDirectory = tmpdir
        fmu.instanceName = "inst1"
        fmu.guid = "{guid}"
        fmu.fmi3InstantiateScheduledExecution = MagicMock(return_value=123)

        # 1. No resources directory -> resourcePath must be None (NULL pointer)
        fmu.instantiate()
        fmu.fmi3InstantiateScheduledExecution.assert_called_once()
        assert fmu.fmi3InstantiateScheduledExecution.call_args[0][2] is None

        # 2. Existing resources directory -> resourcePath must be encoded path
        fmu.fmi3InstantiateScheduledExecution.reset_mock()
        res_dir = os.path.join(tmpdir, "resources")
        os.makedirs(res_dir, exist_ok=True)
        fmu.instantiate()
        fmu.fmi3InstantiateScheduledExecution.assert_called_once()
        expected = (res_dir + os.path.sep).encode("utf-8")
        assert fmu.fmi3InstantiateScheduledExecution.call_args[0][2] == expected

        # 3. Explicit resourcePath parameter -> uses provided path
        fmu.fmi3InstantiateScheduledExecution.reset_mock()
        fmu.instantiate(resourcePath="/custom/res/")
        fmu.fmi3InstantiateScheduledExecution.assert_called_once()
        assert fmu.fmi3InstantiateScheduledExecution.call_args[0][2] == b"/custom/res/"
