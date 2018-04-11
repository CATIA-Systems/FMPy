from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
from fmpy import simulate_fmu
from fmpy.fmi2 import fmi2Warning


class SimulationThread(QThread):

    progressChanged = pyqtSignal(int)
    messageChanged = pyqtSignal(str, str)

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

    def logFMUMessage(self, componentEnvironment, instanceName, status, category, message):

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
                                       fmi_call_logger=self.logFMICall if self.fmiLogging else None,
                                       logger=self.logFMUMessage,
                                       step_finished=self.stepFinished)
        except Exception as e:
            self.messageChanged.emit('error', str(e))

        stopTime = QDateTime.currentMSecsSinceEpoch()
        totalTime = ((stopTime - startTime) / 1000.)

        if self.stopped:
            self.messageChanged.emit('info', 'Simulation stopped after %s s' % totalTime)
        else:
            self.messageChanged.emit('info', 'Simulation took %s s' % totalTime)

    def logFMICall(self, message):
        self.messageChanged.emit('debug', message)
