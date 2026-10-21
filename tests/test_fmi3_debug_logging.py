from unittest.mock import MagicMock
from fmpy.fmi3 import _FMU3


def test_fmi3_set_debug_logging_null_categories():
    """Verify FMI 3.0 standard §2.3 requirement:

    If nCategories = 0, loggingOn applies to all log categories and the
    value of categories must be NULL.
    """
    fmu = _FMU3.__new__(_FMU3)
    fmu.component = 123
    fmu.fmi3SetDebugLogging = MagicMock()

    # Empty categories -> categories argument must be None (NULL pointer)
    fmu.setDebugLogging(False, [])
    fmu.fmi3SetDebugLogging.assert_called_once()
    args = fmu.fmi3SetDebugLogging.call_args[0]
    assert args[1].value is False  # loggingOn
    assert args[2] == 0  # nCategories == 0
    assert args[3] is None  # categories == NULL

    # Non-empty categories -> categories argument must not be None
    fmu.fmi3SetDebugLogging.reset_mock()
    fmu.setDebugLogging(True, ["logEvents"])
    fmu.fmi3SetDebugLogging.assert_called_once()
    args = fmu.fmi3SetDebugLogging.call_args[0]
    assert args[1].value is True  # loggingOn
    assert args[2] == 1  # nCategories == 1
    assert args[3] is not None
