"""FMI 1.0 interface"""

import typing

import ctypes
import types

from typing import Any, Iterable

import os
import pathlib
from ctypes import (
    cdll,
    c_void_p,
    c_uint,
    c_double,
    c_int,
    c_char,
    c_char_p,
    byref,
    c_size_t,
    POINTER,
    cast,
    c_bool,
    c_float,
    c_int8,
    c_int16,
    c_int32,
    c_int64,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    addressof,
    Structure,
    CFUNCTYPE,
)
from . import free, freeLibrary, platform, sharedLibraryExtension, calloc


fmi1Component = c_void_p
fmi1ValueReference = c_uint
fmi1Real = c_double
fmi1Integer = c_int
fmi1Boolean = c_char
fmi1String = c_char_p

fmi1True = b"\x01"
fmi1False = b"\x00"

fmi1UndefinedValueReference = -1

fmi1Status = c_int

fmi1OK = 0
fmi1Warning = 1
fmi1Discard = 2
fmi1Error = 3
fmi1Fatal = 4

fmi1CallbackLoggerTYPE = CFUNCTYPE(
    None, fmi1Component, fmi1String, fmi1Status, fmi1String, fmi1String
)
fmi1CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi1CallbackFreeMemoryTYPE = CFUNCTYPE(None, c_void_p)
# fmi1StepFinishedTYPE           = CFUNCTYPE(None, fmi1Component, fmi1Status)
fmi1StepFinishedTYPE = c_void_p

fmi1StatusKind = c_int

fmi1DoStepStatus = 0
fmi1PendingStatus = 1
fmi1LastSuccessfulTime = 2


class fmi1CallbackFunctions(Structure):
    _fields_ = [
        ("logger", fmi1CallbackLoggerTYPE),
        ("allocateMemory", fmi1CallbackAllocateMemoryTYPE),
        ("freeMemory", fmi1CallbackFreeMemoryTYPE),
        ("stepFinished", fmi1StepFinishedTYPE),
    ]


class fmi1EventInfo(Structure):
    _fields_ = [
        ("iterationConverged", fmi1Boolean),
        ("stateValueReferencesChanged", fmi1Boolean),
        ("stateValuesChanged", fmi1Boolean),
        ("terminateSimulation", fmi1Boolean),
        ("upcomingTimeEvent", fmi1Boolean),
        ("nextEventTime", fmi1Real),
    ]


def printLogMessage(
    component: c_void_p,
    instanceName: bytes,
    status: int,
    category: bytes,
    message: bytes,
):
    """Print the FMU's log messages to the command line (works for both FMI 1.0 and 2.0)"""

    label = ["OK", "WARNING", "DISCARD", "ERROR", "FATAL", "PENDING"][status]
    print(f"[{label}] {message.decode('utf-8')}")


defaultCallbacks = fmi1CallbackFunctions()
defaultCallbacks.logger = fmi1CallbackLoggerTYPE(printLogMessage)
defaultCallbacks.allocateMemory = fmi1CallbackAllocateMemoryTYPE(calloc)
defaultCallbacks.freeMemory = fmi1CallbackFreeMemoryTYPE(free)
defaultCallbacks.stepFinished = None

try:
    from .logging import addLoggerProxy

    addLoggerProxy(byref(defaultCallbacks))
except Exception as e:
    print(f"Failed to add logger proxy function. {e}")


class FMICallException(Exception):
    """Raised when an FMI call fails"""

    def __init__(self, function: str, status: int):
        if status in range(5):
            label = ["ok", "warning", "discard", "error", "fatal", "pending"][status]
        else:
            label = "illegal return code"

        super().__init__(f"{function} failed with status {status} ({label}).")

        self.function = function
        "The name of the FMI function"

        self.status = status
        "The status returned by the FMI function"


class _FMU(object):
    """Base class for all FMUs"""

    def __init__(
        self,
        guid,
        modelIdentifier,
        unzipDirectory,
        instanceName=None,
        libraryPath=None,
        fmiCallLogger=None,
        requireFunctions=True,
    ):
        """
        Parameters:
            guid             the GUI from the modelDescription.xml
            modelIdentifier  the model identifier from the modelDescription.xml
            unzipDirectory   folder where the FMU has been extracted
            instanceName     the name of the FMU instance
            libraryPath      path to the shared library
            fmiCallLogger    logger callback that takes a message as input
            requireFunctions assert required FMI functions in the shared library
        """

        self.guid = guid
        self.modelIdentifier = modelIdentifier
        self.unzipDirectory = unzipDirectory
        self.instanceName = (
            instanceName if instanceName is not None else self.modelIdentifier
        )
        self.fmiCallLogger = fmiCallLogger
        self.requireFunctions = requireFunctions

        self._functions: dict[str, ctypes._FuncPointer] = dict()
        """Functions loaded from the shared library"""

        # remember the current working directory
        work_dir = os.getcwd()

        if libraryPath is None:
            library_dir = os.path.join(unzipDirectory, "binaries", platform)
            library_dir = os.path.abspath(library_dir)
            libraryPath = str(
                os.path.join(library_dir, self.modelIdentifier + sharedLibraryExtension)
            )
        else:
            library_dir = os.path.dirname(libraryPath)

        # check if shared library exists
        if not os.path.isfile(libraryPath):
            raise Exception("Cannot find shared library %s." % libraryPath)

        # change to the library directory as some DLLs expect this to resolve dependencies
        os.chdir(library_dir)

        # load the shared library
        try:
            self.dll = cdll.LoadLibrary(libraryPath)
        except Exception as e:
            raise Exception(f"Failed to load shared library {libraryPath}. {e}")

        # change back to the working directory
        os.chdir(work_dir)

        # load the FMI API functions from the shared library
        self._loadFunctions()

        self.component: c_void_p = None
        """Instance pointer of the FMU"""

        self.callbacks = None
        """Reference to the callbacks struct (to save it from GC)"""

    def freeLibrary(self):
        # unload the shared library
        freeLibrary(self.dll._handle)

    def _log_fmi_args(
        self,
        fname: str,
        argnames: Iterable[str],
        argtypes: Iterable[type],
        args: Iterable,
        restype: Any,
        res: Any,
    ) -> None:
        """Format FMI arguments and pass them to the logger"""

        message = fname + "("

        arguments: list[str] = []

        def struct_to_str(s):
            a = []

            for n, t in s._fields_:
                if t == c_char:
                    v = int.from_bytes(s.iterationConverged, "little")
                else:
                    v = str(getattr(s, n))

                    prefix = "<CFunctionType object at "

                    if v.startswith(prefix) and v.endswith(">"):
                        v = v[len(prefix) : -1]
                    elif v == "None":
                        v = "0x0"

                a.append(f"{n}={v}")

            return f"{type(s).__name__}(" + ", ".join(a) + ")"

        for i, (n, t, v) in enumerate(zip(argnames, argtypes, args)):
            a = n + "="

            if fname == "fmi2Instantiate" and n == "callbacks":
                from .fmi2 import fmi2CallbackFunctions

                a += struct_to_str(cast(v, POINTER(fmi2CallbackFunctions)).contents)
            elif (
                fname in ["fmiInstantiateModel", "fmiInstantiateSlave"]
                and n == "functions"
            ):
                a += struct_to_str(v)
            elif fname in ["fmiInitialize", "fmiEventUpdate"] and n == "eventInfo":
                a += struct_to_str(cast(v, POINTER(fmi1EventInfo)).contents)
            elif fname == "fmi2NewDiscreteStates" and n == "eventInfo":
                from .fmi2 import fmi2EventInfo

                a += struct_to_str(cast(v, POINTER(fmi2EventInfo)).contents)
            elif fname in ["fmi3GetBinary", "fmi3SetBinary"] and n == "values":
                a += (
                    "["
                    + ", ".join([hex(addressof(p.contents) if p else 0) for p in v])
                    + "]"
                )
            elif t == c_char:
                a += str(v[0])
            elif t == c_void_p:
                if isinstance(v, c_void_p):
                    v = v.value
                a += hex(0 if v is None else v)
            elif t == c_bool:
                a += str(v.value)
            elif t == POINTER(c_uint):
                # value references
                if v is None:
                    a += "NULL"
                else:
                    a += "[" + ", ".join(map(str, v)) + "]"
            elif t in [
                POINTER(c_float),
                POINTER(c_double),
                POINTER(c_int8),
                POINTER(c_uint8),
                POINTER(c_int16),
                POINTER(c_uint16),
                POINTER(c_int32),
                POINTER(c_uint32),
                POINTER(c_int64),
                POINTER(c_uint64),
                POINTER(c_bool),
                POINTER(c_char_p),
            ] and hasattr(v, "__len__"):
                # c_*_Array_N
                a += "[" + ", ".join(map(str, v)) + "]"
            elif t == POINTER(c_double) and not hasattr(v, "__len__"):
                if len(args) > i + 1:
                    # double pointers are always flowed by the size of the array
                    arr = v[: args[i + 1]]
                    a += "[" + ", ".join(map(str, arr)) + "]"
                else:
                    # except for fmi3DoStep
                    v_ = cast(v, POINTER(c_double))
                    a += str(str(v_.contents.value))
            elif hasattr(v, "_obj"):
                # byref object
                if hasattr(v._obj, "value"):
                    # pointer (e.g. c_char_p)
                    a += str(v._obj.value)
                else:
                    # struct
                    a += str(v._obj)
            elif hasattr(v, "decode"):
                # UTF-8 byte string
                a += '"' + v.decode("utf-8") + '"'
            else:
                a += str(v)

            arguments.append(a)

        message += ", ".join(arguments) + ")"

        if restype == c_int:
            message += " -> "

            if res == 0:
                message += "OK"
            elif res == 1:
                message += "WARNING"
            elif res == 2:
                message += "DISCARD"
            elif res == 3:
                message += "ERROR"
            elif res == 4:
                message += "FATAL"
            elif res == 5:
                message += "PENDING"
            else:
                message += str(res)
        elif restype == c_void_p:
            message += " -> " + hex(0 if res is None else res)

        self.fmiCallLogger(message)

    def _call(self, fname: str, *args) -> Any:
        """Call and log the FMI API function"""

        f = self._functions[fname]

        res = f(*args)

        if self.fmiCallLogger is not None:
            self._log_fmi_args(fname, f.argnames, f.argtypes, args, f.restype, res)

        if f.restype == c_int:
            # check the status code
            if res > fmi1Warning:
                raise FMICallException(function=fname, status=res)

        return res

    def _loadFunctions(self) -> None:
        """Load the FMI API functions from the shared library"""

        class_name = self.__class__.__name__
        identifier = None

        if class_name.startswith("FMU1"):
            prefix = "fmi1"
            identifier = self.modelIdentifier + "_"
        elif class_name.startswith("FMU2"):
            prefix = "fmi2"
        else:
            prefix = "fmi3"

        import inspect

        for name, value in inspect.getmembers(self):
            if name.startswith(prefix):
                py_fun = getattr(self, name)
                sig = inspect.signature(py_fun)

                c_fun_name = name

                if identifier:
                    c_fun_name = identifier + c_fun_name.replace("fmi1", "fmi")

                c_fun: ctypes._FuncPointer = getattr(self.dll, c_fun_name)

                argnames = []
                argtypes = []

                for param in sig.parameters.values():
                    argnames.append(param.name)
                    import typing

                    if isinstance(param.annotation, types.UnionType):
                        args = typing.get_args(param.annotation)
                        argtypes.append(args[0])
                    else:
                        argtypes.append(param.annotation)

                c_fun.argnames = argnames
                c_fun.argtypes = argtypes

                restype = sig.return_annotation

                if restype is bytes:
                    restype = c_char_p
                elif restype is int:
                    restype = c_int

                c_fun.restype = restype
                self._functions[name] = c_fun


class _FMU1(_FMU):
    """Base class for FMI 1.0 FMUs"""

    def __init__(self, **kwargs):
        super(_FMU1, self).__init__(**kwargs)

    def fmi1GetVersion(self) -> bytes:
        return self._call("fmi1GetVersion")

    def fmi1SetDebugLogging(
        self, component: fmi1Component, loggingOn: fmi1Boolean | bool
    ) -> fmi1Status:
        return self._call("fmi1SetDebugLogging", component, loggingOn)

    # Data Exchange Functions

    def fmi1GetReal(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Real),
    ) -> fmi1Status:
        return self._call("fmi1GetReal", component, vr, nvr, value)

    def fmi1GetInteger(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Integer),
    ) -> fmi1Status:
        return self._call("fmi1GetInteger", component, vr, nvr, value)

    def fmi1GetBoolean(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Boolean),
    ) -> fmi1Status:
        return self._call("fmi1GetBoolean", component, vr, nvr, value)

    def fmi1GetString(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1String),
    ) -> fmi1Status:
        return self._call("fmi1GetString", component, vr, nvr, value)

    def fmi1SetReal(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Real),
    ) -> fmi1Status:
        return self._call("fmi1SetReal", component, vr, nvr, value)

    def fmi1SetInteger(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Integer),
    ) -> fmi1Status:
        return self._call("fmi1SetInteger", component, vr, nvr, value)

    def fmi1SetBoolean(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1Boolean),
    ) -> fmi1Status:
        return self._call("fmi1SetBoolean", component, vr, nvr, value)

    def fmi1SetString(
        self,
        component: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi1String),
    ) -> fmi1Status:
        return self._call("fmi1SetString", component, vr, nvr, value)

    # Inquire version numbers of header files

    def getVersion(self) -> str:
        version = typing.cast(bytes, self.fmi1GetVersion())
        return version.decode("utf-8")

    def setDebugLogging(self, loggingOn):
        self.fmi1SetDebugLogging(self.component, fmi1True if loggingOn else fmi1False)

    # Data Exchange Functions

    def getReal(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))()
        self.fmi1GetReal(self.component, vr, len(vr), value)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))()
        self.fmi1GetInteger(self.component, vr, len(vr), value)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))()
        self.fmi1GetBoolean(self.component, vr, len(vr), value)
        return list(map(lambda b: 0 if b == fmi1False else 1, value))

    def getString(self, vr):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1String * len(vr))()
        self.fmi1GetString(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Real * len(vr))(*value)
        self.fmi1SetReal(self.component, vr, len(vr), value)

    def setInteger(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Integer * len(vr))(*value)
        self.fmi1SetInteger(self.component, vr, len(vr), value)

    def setBoolean(self, vr, value):
        # convert value to a byte string
        s = b""
        for v in value:
            s += fmi1True if v else fmi1False

        vr = (fmi1ValueReference * len(vr))(*vr)
        value = (fmi1Boolean * len(vr))(s)
        self.fmi1SetBoolean(self.component, vr, len(vr), value)

    def setString(self, vr, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        value = map(lambda s: s.encode("utf-8"), value)
        value = (fmi1String * len(vr))(*value)
        self.fmi1SetString(self.component, vr, len(vr), value)


class FMU1Slave(_FMU1):
    """An FMI 1.0 Co-Simulation FMU"""

    def __init__(self, **kwargs):
        super(FMU1Slave, self).__init__(**kwargs)

    # Inquire version numbers of header files

    def fmi1GetTypesPlatform(self) -> bytes:
        return self._call("fmi1GetTypesPlatform")

    # Creation and destruction of slave instances and setting debug status

    def fmi1InstantiateSlave(
        self,
        instanceName: fmi1String,
        guid: fmi1String,
        fmuLocation: fmi1String,
        mimeType: fmi1String,
        timeout: fmi1Real | float,
        visible: fmi1Boolean | bool,
        interactive: fmi1Boolean | bool,
        functions: fmi1CallbackFunctions,
        loggingOn: fmi1Boolean | bool,
    ) -> fmi1Component:
        return self._call(
            "fmi1InstantiateSlave",
            instanceName,
            guid,
            fmuLocation,
            mimeType,
            timeout,
            visible,
            interactive,
            functions,
            loggingOn,
        )

    def fmi1InitializeSlave(
        self,
        component: fmi1Component,
        tStart: fmi1Real | float,
        stopTimeDefined: fmi1Boolean | bool,
        tStop: fmi1Real | float,
    ) -> fmi1String:
        return self._call(
            "fmi1InitializeSlave",
            component,
            tStart,
            stopTimeDefined,
            tStop,
        )

    def fmi1TerminateSlave(self, c: fmi1Component) -> fmi1Status:
        return self._call("fmi1TerminateSlave", c)

    def fmi1ResetSlave(self, c: fmi1Component) -> fmi1Status:
        return self._call("fmi1ResetSlave", c)

    def fmi1FreeSlaveInstance(self, c: fmi1Component) -> None:
        return self._call("fmi1FreeSlaveInstance", c)

    def fmi1SetRealInputDerivatives(
        self,
        c: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        order: POINTER(fmi1Integer),
        value: POINTER(fmi1Real),
    ) -> fmi1String:
        return self._call(
            "fmi1InitializeSlave",
            c,
            vr,
            nvr,
            order,
            value,
        )

    def fmi1GetRealOutputDerivatives(
        self,
        c: fmi1Component,
        vr: POINTER(fmi1ValueReference),
        nvr: c_size_t | int,
        order: POINTER(fmi1Integer),
        value: POINTER(fmi1Real),
    ) -> fmi1String:
        return self._call(
            "fmi1GetRealOutputDerivatives",
            c,
            vr,
            nvr,
            order,
            value,
        )

    def fmi1CancelStep(
        self,
        c: fmi1Component,
    ) -> fmi1String:
        return self._call(
            "fmi1CancelStep",
            c,
        )

    def fmi1DoStep(
        self,
        c: fmi1Component,
        currentCommunicationPoint: fmi1Real | float,
        communicationStepSize: fmi1Real | float,
        newStep: fmi1Boolean | bool,
    ) -> fmi1String:
        return self._call(
            "fmi1DoStep",
            c,
            currentCommunicationPoint,
            communicationStepSize,
            newStep,
        )

    def fmi1GetStatus(
        self,
        c: fmi1Component,
        kind: fmi1StatusKind,
        value: POINTER(fmi1Status),
    ) -> fmi1String:
        return self._call(
            "fmi1GetStatus",
            c,
            kind,
            value,
        )

    def fmi1GetRealStatus(
        self,
        c: fmi1Component,
        kind: fmi1StatusKind,
        value: POINTER(fmi1Real),
    ) -> fmi1String:
        return self._call(
            "fmi1GetRealStatus",
            c,
            kind,
            value,
        )

    def fmi1GetIntegerStatus(
        self,
        c: fmi1Component,
        kind: fmi1StatusKind,
        value: POINTER(fmi1Integer),
    ) -> fmi1String:
        return self._call(
            "fmi1GetIntegerStatus",
            c,
            kind,
            value,
        )

    def fmi1GetBooleanStatus(
        self,
        c: fmi1Component,
        kind: fmi1StatusKind,
        value: POINTER(fmi1Boolean),
    ) -> fmi1String:
        return self._call(
            "fmi1GetBooleanStatus",
            c,
            kind,
            value,
        )

    def fmi1GetStringStatus(
        self,
        c: fmi1Component,
        kind: fmi1StatusKind,
        value: POINTER(fmi1String),
    ) -> fmi1String:
        return self._call(
            "fmi1GetStringStatus",
            c,
            kind,
            value,
        )

    # Creation and destruction of slave instances and setting debug status

    def instantiate(
        self,
        mimeType="application/x-fmu-sharedlibrary",
        timeout=0,
        visible=fmi1False,
        interactive=fmi1False,
        functions=None,
        loggingOn=False,
    ):
        fmuLocation = pathlib.Path(self.unzipDirectory).as_uri()

        self.callbacks = defaultCallbacks if functions is None else functions

        self.component = self.fmi1InstantiateSlave(
            self.instanceName.encode("UTF-8"),
            self.guid.encode("UTF-8"),
            fmuLocation.encode("UTF-8"),
            mimeType.encode("UTF-8"),
            timeout,
            visible,
            interactive,
            self.callbacks,
            fmi1True if loggingOn else fmi1False,
        )

    # Inquire version numbers of header files

    def getTypesPlatform(self):
        types_platform = self.fmi1GetTypesPlatform()
        return types_platform.decode("utf-8")

    # Creation and destruction of slave instances and setting debug status

    def initialize(self, tStart=0.0, stopTime=None):
        stopTimeDefined = fmi1True if stopTime is not None else fmi1False
        tStop = stopTime if stopTime is not None else 0.0
        return self.fmi1InitializeSlave(self.component, tStart, stopTimeDefined, tStop)

    def terminate(self):
        return self.fmi1TerminateSlave(self.component)

    def reset(self):
        return self.fmi1ResetSlave(self.component)

    def freeInstance(self):
        self.fmi1FreeSlaveInstance(self.component)
        self.freeLibrary()

    def setRealInputDerivatives(self, vr, order, value):
        vr = (fmi1ValueReference * len(vr))(*vr)
        order = (fmi1Integer * len(vr))(*order)
        value = (fmi1Real * len(vr))(*value)
        self.fmi1SetRealInputDerivatives(self.component, vr, len(vr), order, value)

    def getRealOutputDerivatives(self, vr, order):
        vr = (fmi1ValueReference * len(vr))(*vr)
        order = (fmi1Integer * len(vr))(*order)
        value = (fmi1Real * len(vr))()
        self.fmi1GetRealOutputDerivatives(self.component, vr, len(vr), order, value)
        return list(value)

    def cancelStep(self):
        return self.fmi1CancelStep(self.component)

    def doStep(
        self, currentCommunicationPoint, communicationStepSize, newStep=fmi1True
    ):
        self.fmi1DoStep(
            self.component, currentCommunicationPoint, communicationStepSize, newStep
        )

    def getStatus(self, kind):
        value = fmi1Status(fmi1OK)
        self.fmi1GetStatus(self.component, kind, byref(value))
        return value

    def getRealStatus(self, kind):
        value = fmi1Real(0.0)
        self.fmi1GetRealStatus(self.component, kind, byref(value))
        return value

    def getIntegerStatus(self, kind):
        value = fmi1Integer(0)
        self.fmi1GetIntegerStatus(self.component, kind, byref(value))
        return value

    def getBooleanStatus(self, kind):
        value = fmi1Boolean(fmi1False)
        self.fmi1GetBooleanStatus(self.component, kind, byref(value))
        return value

    def getStringStatus(self, kind):
        value = fmi1String(b"")
        self.fmi1GetStringStatus(self.component, kind, byref(value))
        return value


class FMU1Model(_FMU1):
    """An FMI 1.0 Model Exchange FMU"""

    def __init__(self, **kwargs):
        super(FMU1Model, self).__init__(**kwargs)

    # Inquire version numbers of header files

    def fmi1GetModelTypesPlatform(self) -> fmi1String:
        return self._call("fmi1GetModelTypesPlatform")

    # Creation and destruction of model instances and setting debug status

    def fmi1InstantiateModel(
        self,
        instanceName: fmi1String,
        guid: fmi1String,
        functions: fmi1CallbackFunctions,
        loggingOn: fmi1Boolean | bool,
    ) -> fmi1Component:
        return self._call(
            "fmi1InstantiateModel", instanceName, guid, functions, loggingOn
        )

    def fmi1FreeModelInstance(self, c: fmi1Component) -> None:
        return self._call("fmi1FreeModelInstance", c)

    def fmi1SetTime(self, c: fmi1Component, time: fmi1Real | float) -> fmi1Status:
        return self._call("fmi1SetTime", c, time)

    # Providing independent variables and re-initialization of caching

    def fmi1SetContinuousStates(
        self, c: fmi1Component, x: POINTER(fmi1Real), nx: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1SetContinuousStates", c, x, nx)

    def fmi1CompletedIntegratorStep(
        self, c: fmi1Component, callEventUpdate: POINTER(fmi1Boolean)
    ) -> fmi1Status:
        return self._call("fmi1CompletedIntegratorStep", c, callEventUpdate)

    # Evaluation of the model equations

    def fmi1Initialize(
        self,
        c: fmi1Component,
        toleranceControlled: fmi1Boolean | bool,
        relativeTolerance: fmi1Real | float,
        eventInfo: POINTER(fmi1EventInfo),
    ) -> fmi1Status:
        return self._call(
            "fmi1Initialize", c, toleranceControlled, relativeTolerance, eventInfo
        )

    def fmi1GetDerivatives(
        self, c: fmi1Component, derivatives: POINTER(fmi1Real), nx: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1GetDerivatives", c, derivatives, nx)

    def fmi1GetEventIndicators(
        self, c: fmi1Component, eventIndicators: POINTER(fmi1Real), ni: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1GetEventIndicators", c, eventIndicators, ni)

    def fmi1EventUpdate(
        self,
        c: fmi1Component,
        intermediateResults: fmi1Boolean | bool,
        eventInfo: POINTER(fmi1EventInfo),
    ) -> fmi1Status:
        return self._call("fmi1EventUpdate", c, intermediateResults, eventInfo)

    def fmi1GetContinuousStates(
        self, c: fmi1Component, states: POINTER(fmi1Real), nx: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1GetContinuousStates", c, states, nx)

    def fmi1GetNominalContinuousStates(
        self, c: fmi1Component, x_nominal: POINTER(fmi1Real), nx: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1GetNominalContinuousStates", c, x_nominal, nx)

    def fmi1GetStateValueReferences(
        self, c: fmi1Component, vrx: POINTER(fmi1ValueReference), nx: c_size_t
    ) -> fmi1Status:
        return self._call("fmi1GetStateValueReferences", c, vrx, nx)

    def fmi1Terminate(self, c: fmi1Component) -> fmi1Status:
        return self._call("fmi1Terminate", c)

    # Inquire version numbers of header files

    def getTypesPlatform(self):
        types_platform = self.fmi1GetModelTypesPlatform()
        return types_platform.decode("utf-8")

    # Creation and destruction of model instances and setting debug status

    def instantiate(self, functions=None, loggingOn=False):
        self.callbacks = defaultCallbacks if functions is None else functions

        self.component = self.fmi1InstantiateModel(
            self.instanceName.encode("UTF-8"),
            self.guid.encode("UTF-8"),
            self.callbacks,
            fmi1True if loggingOn else fmi1False,
        )

        if self.component is None:
            raise Exception("Failed to instantiate model")

    def freeInstance(self):
        self.fmi1FreeModelInstance(self.component)
        self.freeLibrary()

    # Providing independent variables and re-initialization of caching

    def setTime(self, time):
        return self.fmi1SetTime(self.component, time)

    def setContinuousStates(self, states, size):
        return self.fmi1SetContinuousStates(self.component, states, size)

    def completedIntegratorStep(self):
        stepEvent = fmi1Boolean()
        self.fmi1CompletedIntegratorStep(self.component, byref(stepEvent))
        return stepEvent.value != fmi1False

    # Evaluation of the model equations

    def initialize(self, toleranceControlled=fmi1False, relativeTolerance=0.0):
        eventInfo = fmi1EventInfo()
        self.fmi1Initialize(
            self.component, toleranceControlled, relativeTolerance, byref(eventInfo)
        )
        return (
            eventInfo.iterationConverged != fmi1False,
            eventInfo.stateValueReferencesChanged != fmi1False,
            eventInfo.stateValuesChanged != fmi1False,
            eventInfo.terminateSimulation != fmi1False,
            eventInfo.upcomingTimeEvent != fmi1False,
            eventInfo.nextEventTime,
        )

    def getDerivatives(self, derivatives, size):
        return self.fmi1GetDerivatives(self.component, derivatives, size)

    def getEventIndicators(self, eventIndicators, size):
        return self.fmi1GetEventIndicators(self.component, eventIndicators, size)

    def eventUpdate(self, intermediateResults=fmi1False):
        eventInfo = fmi1EventInfo()
        self.fmi1EventUpdate(self.component, intermediateResults, byref(eventInfo))
        return (
            eventInfo.iterationConverged != fmi1False,
            eventInfo.stateValueReferencesChanged != fmi1False,
            eventInfo.stateValuesChanged != fmi1False,
            eventInfo.terminateSimulation != fmi1False,
            eventInfo.upcomingTimeEvent != fmi1False,
            eventInfo.nextEventTime,
        )

    def getContinuousStates(self, states, size):
        return self.fmi1GetContinuousStates(self.component, states, size)

    def getNominalContinuousStates(self, x_nominal, size):
        return self.fmi1GetNominalContinuousStates(self.component, x_nominal, size)

    def getStateValueReferences(self, vrx, size):
        return self.fmi1GetStateValueReferences(self.component, vrx, size)

    def terminate(self):
        return self.fmi1Terminate(self.component)
