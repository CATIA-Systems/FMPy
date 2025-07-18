"""FMI 2.0 interface"""

from ctypes import (
    c_void_p,
    c_uint,
    c_double,
    c_int,
    c_char,
    c_char_p,
    byref,
    c_size_t,
    POINTER,
    Structure,
    CFUNCTYPE,
    create_string_buffer,
)

import pathlib

from . import free, calloc
from .fmi1 import _FMU, printLogMessage

fmi2Component = c_void_p
fmi2ComponentEnvironment = c_void_p
fmi2FMUstate = c_void_p
fmi2ValueReference = c_uint
fmi2Real = c_double
fmi2Integer = c_int
fmi2Boolean = c_int
fmi2Char = c_char
fmi2String = c_char_p
fmi2Type = c_int
fmi2Byte = c_char

fmi2Status = c_int

fmi2OK = 0
fmi2Warning = 1
fmi2Discard = 2
fmi2Error = 3
fmi2Fatal = 4
fmi2Pending = 5

fmi2CallbackLoggerTYPE = CFUNCTYPE(
    None, fmi2ComponentEnvironment, fmi2String, fmi2Status, fmi2String, fmi2String
)
fmi2CallbackAllocateMemoryTYPE = CFUNCTYPE(c_void_p, c_size_t, c_size_t)
fmi2CallbackFreeMemoryTYPE = CFUNCTYPE(None, c_void_p)
fmi2StepFinishedTYPE = CFUNCTYPE(None, fmi2ComponentEnvironment, fmi2Status)

fmi2ModelExchange = 0
fmi2CoSimulation = 1

fmi2True = 1
fmi2False = 0

fmi2StatusKind = c_int

fmi2DoStepStatus = 0
fmi2PendingStatus = 1
fmi2LastSuccessfulTime = 2
fmi2Terminated = 3


class fmi2CallbackFunctions(Structure):
    _fields_ = [
        ("logger", fmi2CallbackLoggerTYPE),
        ("allocateMemory", fmi2CallbackAllocateMemoryTYPE),
        ("freeMemory", fmi2CallbackFreeMemoryTYPE),
        ("stepFinished", fmi2StepFinishedTYPE),
        ("componentEnvironment", fmi2ComponentEnvironment),
    ]


class fmi2EventInfo(Structure):
    _fields_ = [
        ("newDiscreteStatesNeeded", fmi2Boolean),
        ("terminateSimulation", fmi2Boolean),
        ("nominalsOfContinuousStatesChanged", fmi2Boolean),
        ("valuesOfContinuousStatesChanged", fmi2Boolean),
        ("nextEventTimeDefined", fmi2Boolean),
        ("nextEventTime", fmi2Real),
    ]


defaultCallbacks = fmi2CallbackFunctions()
defaultCallbacks.logger = fmi2CallbackLoggerTYPE(printLogMessage)
defaultCallbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(calloc)
defaultCallbacks.freeMemory = fmi2CallbackFreeMemoryTYPE(free)

try:
    from .logging import addLoggerProxy

    addLoggerProxy(byref(defaultCallbacks))
except Exception as e:
    print(f"Failed to add logger proxy function. {e}")


class _FMU2(_FMU):
    """Base class for FMI 2.0 FMUs"""

    def __init__(self, **kwargs):
        super(_FMU2, self).__init__(**kwargs)

    # Inquire version numbers of header files and setting logging status

    def fmi2GetTypesPlatform(self) -> bytes:
        return self._call("fmi2GetTypesPlatform")

    def fmi2GetVersion(self) -> bytes:
        return self._call("fmi2GetVersion")

    def fmi2SetDebugLogging(
        self,
        c: fmi2Component,
        loggingOn: fmi2Boolean | bool | int,
        nCategories: c_size_t | int,
        categories: POINTER(fmi2String),
    ) -> fmi2Status:
        return self._call(
            "fmi2SetDebugLogging",
            c,
            loggingOn,
            nCategories,
            categories,
        )

    def fmi2FreeInstance(self, c: fmi2Component) -> None:
        self._call("fmi2FreeInstance", c)

    # Enter and exit initialization mode, terminate and reset

    def fmi2SetupExperiment(
        self,
        c: fmi2Component,
        toleranceDefined: fmi2Boolean | bool | int,
        tolerance: fmi2Real | float,
        startTime: fmi2Real | float,
        stopTimeDefined: fmi2Boolean | bool | int,
        stopTime: fmi2Real | float,
    ) -> int:
        return self._call(
            "fmi2SetupExperiment",
            c,
            toleranceDefined,
            tolerance,
            startTime,
            stopTimeDefined,
            stopTime,
        )

    def fmi2EnterInitializationMode(self, c: fmi2Component) -> int:
        return self._call("fmi2EnterInitializationMode", c)

    def fmi2ExitInitializationMode(self, c: fmi2Component) -> int:
        return self._call("fmi2ExitInitializationMode", c)

    def fmi2Terminate(self, c: fmi2Component) -> int:
        return self._call("fmi2Terminate", c)

    def fmi2Reset(self, c: fmi2Component) -> int:
        return self._call("fmi2Reset", c)

    # Creation and destruction of FMU instances and setting debug status

    def fmi2Instantiate(
        self,
        instanceName: fmi2String | bytes,
        fmuType: fmi2Type | int,
        guid: fmi2String | bytes,
        resourceLocation: fmi2String | bytes,
        callbacks: POINTER(fmi2CallbackFunctions),
        visible: fmi2Boolean | bool | int,
        loggingOn: fmi2Boolean | bool | int,
    ) -> fmi2Component:
        return self._call(
            "fmi2Instantiate",
            instanceName,
            fmuType,
            guid,
            resourceLocation,
            callbacks,
            visible,
            loggingOn,
        )

    # Getting and setting variable values

    def fmi2GetReal(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Real),
    ) -> int:
        return self._call("fmi2GetReal", c, vr, nvr, value)

    def fmi2GetInteger(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Integer),
    ) -> int:
        return self._call("fmi2GetInteger", c, vr, nvr, value)

    def fmi2GetBoolean(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Boolean),
    ) -> int:
        return self._call("fmi2GetBoolean", c, vr, nvr, value)

    def fmi2GetString(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2String),
    ) -> int:
        return self._call("fmi2GetString", c, vr, nvr, value)

    def fmi2SetReal(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Real),
    ) -> int:
        return self._call("fmi2SetReal", c, vr, nvr, value)

    def fmi2SetInteger(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Integer),
    ) -> int:
        return self._call("fmi2SetInteger", c, vr, nvr, value)

    def fmi2SetBoolean(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2Boolean),
    ) -> int:
        return self._call("fmi2SetBoolean", c, vr, nvr, value)

    def fmi2SetString(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        value: POINTER(fmi2String),
    ) -> int:
        return self._call("fmi2SetString", c, vr, nvr, value)

    # Getting and setting the internal FMU state

    def fmi2GetFMUstate(
        self,
        c: fmi2Component,
        FMUstate: POINTER(fmi2FMUstate),
    ) -> int:
        return self._call("fmi2GetFMUstate", c, FMUstate)

    def fmi2SetFMUstate(
        self,
        c: fmi2Component,
        FMUstate: fmi2FMUstate,
    ) -> int:
        return self._call("fmi2SetFMUstate", c, FMUstate)

    def fmi2FreeFMUstate(
        self,
        c: fmi2Component,
        FMUstate: POINTER(fmi2FMUstate),
    ) -> int:
        return self._call("fmi2FreeFMUstate", c, FMUstate)

    def fmi2SerializedFMUstateSize(
        self,
        c: fmi2Component,
        FMUstate: fmi2FMUstate,
        size: POINTER(c_size_t),
    ) -> int:
        return self._call("fmi2SerializedFMUstateSize", c, FMUstate, size)

    def fmi2SerializeFMUstate(
        self,
        c: fmi2Component,
        FMUstate: fmi2FMUstate,
        serializedState: POINTER(fmi2Byte),
        size: c_size_t | int,
    ) -> int:
        return self._call("fmi2SerializeFMUstate", c, FMUstate, serializedState, size)

    def fmi2DeSerializeFMUstate(
        self,
        c: fmi2Component,
        serializedState: POINTER(fmi2Byte),
        size: c_size_t | int,
        FMUstate: POINTER(fmi2FMUstate),
    ) -> int:
        return self._call("fmi2DeSerializeFMUstate", c, serializedState, size, FMUstate)

    # Getting partial derivatives

    def fmi2GetDirectionalDerivative(
        self,
        c: fmi2Component,
        vUnknown_ref: POINTER(fmi2ValueReference),
        nUnknown: c_size_t | int,
        vKnown_ref: POINTER(fmi2ValueReference),
        nKnown: c_size_t | int,
        dvKnown: POINTER(fmi2Real),
        dvUnknown: POINTER(fmi2Real),
    ) -> int:
        return self._call(
            "fmi2GetDirectionalDerivative",
            c,
            vUnknown_ref,
            nUnknown,
            vKnown_ref,
            nKnown,
            dvKnown,
            dvUnknown,
        )

    # Inquire version numbers of header files and setting logging status

    def getTypesPlatform(self):
        types_platform = self.fmi2GetTypesPlatform()
        return types_platform.decode("utf-8")

    def getVersion(self):
        version = self.fmi2GetVersion()
        return version.decode("utf-8")

    def setDebugLogging(self, loggingOn, categories):
        categories_ = (fmi2String * len(categories))()
        categories_[:] = [c.encode("utf-8") for c in categories]
        self.fmi2SetDebugLogging(
            self.component,
            fmi2True if loggingOn else fmi2False,
            len(categories),
            categories_,
        )

    # Creation and destruction of FMU instances and setting debug status

    def instantiate(self, visible=False, callbacks=None, loggingOn=False):
        kind = fmi2ModelExchange if isinstance(self, FMU2Model) else fmi2CoSimulation
        resourceLocation = pathlib.Path(self.unzipDirectory, "resources").as_uri()

        self.callbacks = defaultCallbacks if callbacks is None else callbacks

        self.component = self.fmi2Instantiate(
            self.instanceName.encode("utf-8"),
            kind,
            self.guid.encode("utf-8"),
            resourceLocation.encode("utf-8"),
            byref(self.callbacks),
            visible,
            loggingOn,
        )

        if self.component is None:
            raise Exception("Failed to instantiate model")

    def freeInstance(self):
        self.fmi2FreeInstance(self.component)
        self.freeLibrary()

    # Enter and exit initialization mode, terminate and reset

    def setupExperiment(self, tolerance=None, startTime=0.0, stopTime=None):
        toleranceDefined = fmi2True if tolerance is not None else fmi2False

        if tolerance is None:
            tolerance = 0.0

        stopTimeDefined = fmi2True if stopTime is not None else fmi2False

        if stopTime is None:
            stopTime = 0.0

        return self.fmi2SetupExperiment(
            self.component,
            toleranceDefined,
            tolerance,
            startTime,
            stopTimeDefined,
            stopTime,
        )

    def enterInitializationMode(self):
        return self.fmi2EnterInitializationMode(self.component)

    def exitInitializationMode(self):
        return self.fmi2ExitInitializationMode(self.component)

    def terminate(self):
        return self.fmi2Terminate(self.component)

    def reset(self):
        return self.fmi2Reset(self.component)

    # Getting and setting variable values

    def getReal(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))()
        self.fmi2GetReal(self.component, vr, len(vr), value)
        return list(value)

    def getInteger(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Integer * len(vr))()
        self.fmi2GetInteger(self.component, vr, len(vr), value)
        return list(value)

    def getBoolean(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Boolean * len(vr))()
        self.fmi2GetBoolean(self.component, vr, len(vr), value)
        return list(value)

    def getString(self, vr):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2String * len(vr))()
        self.fmi2GetString(self.component, vr, len(vr), value)
        return list(value)

    def setReal(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Real * len(vr))(*value)
        self.fmi2SetReal(self.component, vr, len(vr), value)

    def setInteger(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Integer * len(vr))(*value)
        self.fmi2SetInteger(self.component, vr, len(vr), value)

    def setBoolean(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = (fmi2Boolean * len(vr))(*value)
        self.fmi2SetBoolean(self.component, vr, len(vr), value)

    def setString(self, vr, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        value = map(lambda s: s.encode("utf-8") if s is not None else s, value)
        value = (fmi2String * len(vr))(*value)
        self.fmi2SetString(self.component, vr, len(vr), value)

    # Getting and setting the internal FMU state

    def getFMUstate(self):
        state = fmi2FMUstate()
        self.fmi2GetFMUstate(self.component, byref(state))
        return state

    getFMUState = getFMUstate  # alias for the FMI 3.0 name

    def setFMUstate(self, state):
        self.fmi2SetFMUstate(self.component, state)

    setFMUState = setFMUstate

    def freeFMUstate(self, state):
        self.fmi2FreeFMUstate(self.component, byref(state))

    freeFMUState = freeFMUstate

    def serializeFMUstate(self, state):
        """Serialize an FMU state

        Parameters:
            state   the FMU state

        Returns:
            the serialized state as a byte string
        """

        size = c_size_t()
        self.fmi2SerializedFMUstateSize(self.component, state, byref(size))
        serializedState = create_string_buffer(size.value)
        self.fmi2SerializeFMUstate(self.component, state, serializedState, size)
        return serializedState.raw

    serializeFMUState = serializeFMUstate

    def deSerializeFMUstate(self, serializedState, state=None):
        """De-serialize an FMU state

        Parameters:
            serializedState   the serialized state as a byte string
            state             previous FMU state for re-use (optional)

        Returns:
            the de-serialized FMU state
        """
        if state is None:
            state = fmi2FMUstate()
        buffer = create_string_buffer(serializedState, size=len(serializedState))
        self.fmi2DeSerializeFMUstate(self.component, buffer, len(buffer), byref(state))
        return state

    deserializeFMUState = deSerializeFMUstate

    # Getting partial derivatives

    def getDirectionalDerivative(self, vUnknown_ref, vKnown_ref, dvKnown):
        """Get partial derivatives

        Parameters:
            vUnknown_ref    a list of value references of the unknowns
            vKnown_ref      a list of value references of the knowns
            dvKnown         a list of delta values (one per known)

        Returns:
            a list of the partial derivatives (one per unknown)
        """

        vUnknown_ref = (fmi2ValueReference * len(vUnknown_ref))(*vUnknown_ref)
        vKnown_ref = (fmi2ValueReference * len(vKnown_ref))(*vKnown_ref)
        dvKnown = (fmi2Real * len(dvKnown))(*dvKnown)
        dvUnknown = (fmi2Real * len(vUnknown_ref))()

        self.fmi2GetDirectionalDerivative(
            self.component,
            vUnknown_ref,
            len(vUnknown_ref),
            vKnown_ref,
            len(vKnown_ref),
            dvKnown,
            dvUnknown,
        )

        return list(dvUnknown)


class FMU2Model(_FMU2):
    """An FMI 2.0 Model Exchange FMU"""

    def __init__(self, **kwargs):
        super(FMU2Model, self).__init__(**kwargs)

    # Enter and exit the different modes

    def fmi2EnterEventMode(self, c: fmi2Component) -> int:
        return self._call("fmi2EnterEventMode", c)

    def fmi2NewDiscreteStates(
        self, c: fmi2Component, eventInfo: POINTER(fmi2EventInfo)
    ) -> int:
        return self._call("fmi2NewDiscreteStates", c, eventInfo)

    def fmi2EnterContinuousTimeMode(self, c: fmi2Component) -> int:
        return self._call("fmi2EnterContinuousTimeMode", c)

    def fmi2CompletedIntegratorStep(
        self,
        c: fmi2Component,
        noSetFMUStatePriorToCurrentPoint: fmi2Boolean | bool | int,
        enterEventMode: POINTER(fmi2Boolean),
        terminateSimulation: POINTER(fmi2Boolean),
    ) -> int:
        return self._call(
            "fmi2CompletedIntegratorStep",
            c,
            noSetFMUStatePriorToCurrentPoint,
            enterEventMode,
            terminateSimulation,
        )

    # Providing independent variables and re-initialization of caching

    def fmi2SetTime(self, c: fmi2Component, time: fmi2Real | float) -> int:
        return self._call("fmi2SetTime", c, time)

    def fmi2SetContinuousStates(
        self, c: fmi2Component, x: POINTER(fmi2Real), nx: c_size_t | int
    ) -> int:
        return self._call("fmi2SetContinuousStates", c, x, nx)

    # Evaluation of the model equations

    def fmi2GetDerivatives(
        self, c: fmi2Component, derivatives: POINTER(fmi2Real), nx: c_size_t | int
    ) -> int:
        return self._call("fmi2GetDerivatives", c, derivatives, nx)

    def fmi2GetEventIndicators(
        self, c: fmi2Component, eventIndicators: POINTER(fmi2Real), ni: c_size_t | int
    ) -> int:
        return self._call("fmi2GetEventIndicators", c, eventIndicators, ni)

    def fmi2GetContinuousStates(
        self, c: fmi2Component, x: POINTER(fmi2Real), nx: c_size_t | int
    ) -> int:
        return self._call("fmi2GetContinuousStates", c, x, nx)

    def fmi2GetNominalsOfContinuousStates(
        self, c: fmi2Component, x_nominal: POINTER(fmi2Real), nx: c_size_t | int
    ) -> int:
        return self._call("fmi2GetNominalsOfContinuousStates", c, x_nominal, nx)

    # Enter and exit the different modes

    def enterEventMode(self):
        return self.fmi2EnterEventMode(self.component)

    def newDiscreteStates(self):
        eventInfo = fmi2EventInfo()

        self.fmi2NewDiscreteStates(self.component, byref(eventInfo))

        return (
            eventInfo.newDiscreteStatesNeeded != fmi2False,
            eventInfo.terminateSimulation != fmi2False,
            eventInfo.nominalsOfContinuousStatesChanged != fmi2False,
            eventInfo.valuesOfContinuousStatesChanged != fmi2False,
            eventInfo.nextEventTimeDefined != fmi2False,
            eventInfo.nextEventTime,
        )

    def enterContinuousTimeMode(self):
        return self.fmi2EnterContinuousTimeMode(self.component)

    def completedIntegratorStep(self, noSetFMUStatePriorToCurrentPoint=fmi2True):
        enterEventMode = fmi2Boolean()
        terminateSimulation = fmi2Boolean()
        self.fmi2CompletedIntegratorStep(
            self.component,
            noSetFMUStatePriorToCurrentPoint,
            byref(enterEventMode),
            byref(terminateSimulation),
        )
        return enterEventMode.value != fmi2False, terminateSimulation.value != fmi2False

    # Providing independent variables and re-initialization of caching

    def setTime(self, time):
        return self.fmi2SetTime(self.component, time)

    def setContinuousStates(self, x, nx):
        return self.fmi2SetContinuousStates(self.component, x, nx)

    # Evaluation of the model equations

    def getDerivatives(self, dx, nx):
        return self.fmi2GetDerivatives(self.component, dx, nx)

    def getEventIndicators(self, z, nz):
        return self.fmi2GetEventIndicators(self.component, z, nz)

    def getContinuousStates(self, x, nx):
        return self.fmi2GetContinuousStates(self.component, x, nx)

    def getNominalsOfContinuousStates(self, x_nominal, nx):
        return self.fmi2GetNominalsOfContinuousStates(self.component, x_nominal, nx)


class FMU2Slave(_FMU2):
    """An FMI 2.0 Co-Simulation FMU"""

    def __init__(self, instanceName=None, **kwargs):
        kwargs["instanceName"] = instanceName

        super(FMU2Slave, self).__init__(**kwargs)

        # Simulating the slave

    def fmi2SetRealInputDerivatives(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        order: POINTER(fmi2Integer),
        value: POINTER(fmi2Real),
    ) -> int:
        return self._call("fmi2SetRealInputDerivatives", c, vr, nvr, order, value)

    def fmi2GetRealOutputDerivatives(
        self,
        c: fmi2Component,
        vr: POINTER(fmi2ValueReference),
        nvr: c_size_t | int,
        order: POINTER(fmi2Integer),
        value: POINTER(fmi2Real),
    ) -> int:
        return self._call("fmi2GetRealOutputDerivatives", c, vr, nvr, order, value)

    def fmi2DoStep(
        self,
        c: fmi2Component,
        currentCommunicationPoint: fmi2Real | float,
        communicationStepSize: fmi2Real | float,
        noSetFMUStatePriorToCurrentPoint: fmi2Boolean | bool | int,
    ) -> int:
        return self._call(
            "fmi2DoStep",
            c,
            currentCommunicationPoint,
            communicationStepSize,
            noSetFMUStatePriorToCurrentPoint,
        )

    def fmi2CancelStep(self, c: fmi2Component) -> int:
        return self._call("fmi2CancelStep", c)

    # Inquire slave status

    def fmi2GetStatus(
        self, c: fmi2Component, kind: fmi2StatusKind | int, value: POINTER(fmi2Status)
    ) -> int:
        return self._call("fmi2GetStatus", c, kind, value)

    def fmi2GetRealStatus(
        self, c: fmi2Component, kind: fmi2StatusKind | int, value: POINTER(fmi2Real)
    ) -> int:
        return self._call("fmi2GetRealStatus", c, kind, value)

    def fmi2GetIntegerStatus(
        self, c: fmi2Component, kind: fmi2StatusKind | int, value: POINTER(fmi2Integer)
    ) -> int:
        return self._call("fmi2GetIntegerStatus", c, kind, value)

    def fmi2GetBooleanStatus(
        self, c: fmi2Component, kind: fmi2StatusKind | int, value: POINTER(fmi2Boolean)
    ) -> int:
        return self._call("fmi2GetBooleanStatus", c, kind, value)

    def fmi2GetStringStatus(
        self, c: fmi2Component, kind: fmi2StatusKind | int, value: POINTER(fmi2String)
    ) -> int:
        return self._call("fmi2GetStringStatus", c, kind, value)

    # Simulating the slave

    def setRealInputDerivatives(self, vr, order, value):
        vr = (fmi2ValueReference * len(vr))(*vr)
        order = (fmi2Integer * len(vr))(*order)
        value = (fmi2Real * len(vr))(*value)
        self.fmi2SetRealInputDerivatives(self.component, vr, len(vr), order, value)

    def getRealOutputDerivatives(self, vr, order):
        vr = (fmi2ValueReference * len(vr))(*vr)
        order = (fmi2Integer * len(vr))(*order)
        value = (fmi2Real * len(vr))()
        self.fmi2GetRealOutputDerivatives(self.component, vr, len(vr), order, value)
        return list(value)

    def doStep(
        self,
        currentCommunicationPoint,
        communicationStepSize,
        noSetFMUStatePriorToCurrentPoint=fmi2True,
    ):
        self.fmi2DoStep(
            self.component,
            currentCommunicationPoint,
            communicationStepSize,
            noSetFMUStatePriorToCurrentPoint,
        )

    def cancelStep(self):
        self.fmi2CancelStep(self.component)

    # Inquire slave status

    def getStatus(self, kind):
        value = fmi2Status(fmi2OK)
        self.fmi2GetStatus(self.component, kind, byref(value))
        return value.value

    def getRealStatus(self, kind):
        value = fmi2Real(0.0)
        self.fmi2GetRealStatus(self.component, kind, byref(value))
        return value.value

    def getIntegerStatus(self, kind):
        value = fmi2Integer(0)
        self.fmi2GetIntegerStatus(self.component, kind, byref(value))
        return value.value

    def getBooleanStatus(self, kind):
        value = fmi2Boolean(fmi2False)
        self.fmi2GetBooleanStatus(self.component, kind, byref(value))
        return bool(value.value)

    def getStringStatus(self, kind):
        value = fmi2String(b"")
        self.fmi2GetStringStatus(self.component, kind, byref(value))
        return value.value.decode("utf-8")
