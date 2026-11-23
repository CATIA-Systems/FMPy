from PySide6.QtCore import QThread, QDateTime
from PySide6.QtCore import Signal

from fmpy import simulate_fmu
from fmpy.fmi2 import fmi2Warning


class SimulationThread(QThread):

    progressChanged = Signal(int)
    messageChanged = Signal(str, str)

    def __init__(self, filename, fmiType, stopTime, solver, stepSize, relativeTolerance, outputInterval, startValues, applyDefaultStartValues, input, output, debugLogging, fmiLogging, parent=None):

        super(SimulationThread, self).__init__(parent)

        self.filename = filename
        self.fmiType = fmiType
        self.stopTime = stopTime
        self.solver = solver
        self.stepSize = stepSize
        self.relativeTolerance = relativeTolerance
        self.outputInterval = outputInterval
        self.startValues = startValues
        self.applyDefaultStartValues = applyDefaultStartValues
        self.input = input
        self.output = output
        self.debugLogging = debugLogging
        self.fmiLogging = fmiLogging
        self.progress = 0
        self.stopped = False

        self.cols = []
        self.rows = []
        self.result = None

    def stop(self):
        self.stopped = True

    def logFMUMessage(self, *args):
        # works with FMI 1.0, 2.0, and 3.0

        status = args[-3]
        message = args[-1]

        if status == fmi2Warning:
            level = 'warning'
        elif status > fmi2Warning:
            level = 'error'
        else:
            level = 'info'

        self.messageChanged.emit(level, message.decode('utf-8'))

    def logFMICall(self, message):
        self.messageChanged.emit('debug', message)

    def stepFinished(self, time, recorder):

        progress = int((time / self.stopTime) * 100)

        if progress > self.progress:
            self.progress = progress
            self.progressChanged.emit(progress)

        # self.msleep(10)

        self.cols = recorder.cols
        self.rows = recorder.rows

        return not self.stopped

    def run(self):

        startTime = QDateTime.currentMSecsSinceEpoch()

        try:
            self.simulate()
        except Exception as e:
            self.messageChanged.emit('error', str(e))

        stopTime = QDateTime.currentMSecsSinceEpoch()
        totalTime = ((stopTime - startTime) / 1000.)

        if self.stopped:
            self.messageChanged.emit('info', 'Simulation stopped after %s s' % totalTime)
        else:
            self.messageChanged.emit('info', 'Simulation took %s s' % totalTime)

    def simulate(self):
        self.result = simulate_fmu(self.filename,
                                   stop_time=self.stopTime,
                                   solver=self.solver,
                                   step_size=self.stepSize,
                                   relative_tolerance=self.relativeTolerance,
                                   output_interval=self.outputInterval,
                                   fmi_type=self.fmiType,
                                   start_values=self.startValues,
                                   apply_default_start_values=self.applyDefaultStartValues,
                                   input=self.input,
                                   output=self.output,
                                   debug_logging=self.debugLogging,
                                   visible=True,
                                   fmi_call_logger=self.logFMICall if self.fmiLogging else None,
                                   logger=self.logFMUMessage,
                                   step_finished=self.stepFinished)

    def logFMICall(self, message):
        self.messageChanged.emit('debug', message)


def fmi_rs_available() -> bool:
    """ Returns True if the fmi-rs simulation engine (package fmi_rs) is installed """
    from importlib.util import find_spec
    return find_spec('fmi_rs') is not None


def recorded_columns(model_description):
    """ Returns the NumPy dtype columns of the variables recorded by FmiRsSimulationThread
    (numeric variables only, like FMPy's Recorder) """

    import numpy as np

    if model_description.fmiVersion == '2.0':
        dtypes = {'Real': np.float64, 'Integer': np.int32, 'Enumeration': np.int32, 'Boolean': np.bool_}
    else:
        dtypes = {
            'Float32': np.float32, 'Float64': np.float64,
            'Int8': np.int8, 'UInt8': np.uint8, 'Int16': np.int16, 'UInt16': np.uint16,
            'Int32': np.int32, 'UInt32': np.uint32, 'Int64': np.int64, 'UInt64': np.uint64,
            'Enumeration': np.int64, 'Boolean': np.bool_,
        }

    cols = [('time', np.float64)]

    for variable in model_description.modelVariables:

        if variable.name == 'time' or variable.type not in dtypes:
            continue  # "time" is reserved for the simulation time

        dtype = dtypes[variable.type]

        if variable.shape:
            # fmi-rs returns arrays flattened
            cols.append((variable.name, dtype, (int(np.prod(variable.shape)),)))
        else:
            cols.append((variable.name, dtype))

    return cols


class FmiRsSimulationThread(SimulationThread):
    """ Runs the simulation with the fmi-rs engine (FMI 2.0 and 3.0) """

    def __init__(self, *args, inputFilename=None, **kwargs):
        super(FmiRsSimulationThread, self).__init__(*args, **kwargs)
        self.inputFilename = inputFilename

    def logFMUMessage(self, status, category, message):

        if status == fmi2Warning:
            level = 'warning'
        elif status > fmi2Warning:
            level = 'error'
        else:
            level = 'info'

        self.messageChanged.emit(level, message)

    def stepFinished(self, time, row):

        progress = int((time / self.stopTime) * 100)

        if progress > self.progress:
            self.progress = progress
            self.progressChanged.emit(progress)

        # fill the columns of the aliases with the values of the original variables
        self.rows.append(tuple(row[i] for i in self.indices))

        return not self.stopped

    def simulate(self):

        import fmi_rs
        import numpy as np
        from fmpy import read_model_description

        if self.applyDefaultStartValues:
            self.messageChanged.emit('warning', "Applying the default start values is not supported by fmi-rs and was skipped.")

        model_description = read_model_description(self.filename)

        self.cols = recorded_columns(model_description)

        # fmi-rs does not record FMI 3.0 aliases, so record the original variables instead
        variables = dict((v.name, v) for v in model_description.modelVariables)
        names = [col[0] for col in self.cols[1:]]
        output = [name for name in names if variables[name].alias is None]
        self.indices = [0] + [output.index(name if variables[name].alias is None else variables[name].alias.name) + 1 for name in names]

        fmi_rs.simulate(self.filename,
                        fmi_type=self.fmiType,
                        stop_time=self.stopTime,
                        solver=self.solver,
                        step_size=self.stepSize if self.solver == 'Euler' else None,
                        relative_tolerance=self.relativeTolerance,
                        output_interval=self.outputInterval,
                        start_values=self.startValues,
                        input_file=self.inputFilename,
                        output=output,
                        debug_logging=self.debugLogging,
                        logger=self.logFMUMessage,
                        fmi_call_logger=self.logFMICall if self.fmiLogging else None,
                        step_finished=self.stepFinished)

        self.result = np.array(self.rows, dtype=np.dtype(self.cols))
