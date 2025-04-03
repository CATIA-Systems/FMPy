""" Entry point for the graphical user interface """
import shutil

try:
    from . import compile_resources
    compile_resources()
except Exception as e:
    print("Failed to compiled resources. %s" % e)

import os
import sys

from PySide6.QtCore import QCoreApplication, QDir, Qt, QUrl, QSettings, QPoint, QTimer, QStandardPaths, \
    QPointF, QBuffer, QIODevice, QSize
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLineEdit, QComboBox, QFileDialog, QLabel, QVBoxLayout, \
    QMenu, QMessageBox, QProgressBar, QDialog, QGraphicsScene, QGraphicsItemGroup, QGraphicsRectItem, \
    QGraphicsTextItem, QGraphicsPathItem, QFileSystemModel
from PySide6.QtGui import QDesktopServices, QPixmap, QIcon, QDoubleValidator, QColor, QFont, QPen, QFontMetricsF, \
    QPolygonF, QPainterPath, QGuiApplication
from PySide6.QtCore import Signal

from fmpy.gui.generated.MainWindow import Ui_MainWindow
import fmpy
from fmpy import read_model_description, supported_platforms, platform
from fmpy.model_description import ScalarVariable
from fmpy.util import can_simulate, remove_source_code

from fmpy.gui.model import VariablesTableModel, VariablesTreeModel, VariablesModel, VariablesFilterModel
from fmpy.gui.log import Log, LogMessagesFilterProxyModel

QCoreApplication.setApplicationVersion(fmpy.__version__)
QCoreApplication.setOrganizationName("CATIA-Systems")
QCoreApplication.setApplicationName("FMPy")

import pyqtgraph as pg

# pg.setConfigOptions(foreground='r', antialias=True)

COLLAPSABLE_COLUMNS = ['Type', 'Dimensions', 'Value Reference', 'Initial', 'Causality', 'Variability', 'Nominal', 'Min', 'Max']


class ClickableLabel(QLabel):
    """ A QLabel that shows a pointing hand cursor and emits a *clicked* event when clicked """

    clicked = Signal()

    def __init__(self, parent=None):
        super(ClickableLabel, self).__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, ev):
        self.clicked.emit()
        super(ClickableLabel, self).mousePressEvent(ev)


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)

        from .generated.AboutDialog import Ui_Dialog
        from .. import __version__, platform, __file__
        import sys
        import os

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        # hide the question mark button
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        flags |= Qt.MSWindowsFixedSizeDialogHint
        self.setWindowFlags(flags)

        self.ui.fmpyVersionLabel.setText(__version__)
        self.ui.fmiPlatformLabel.setText(platform)
        self.ui.installationPathLabel.setText(os.path.dirname(__file__))
        self.ui.pythonInterpreterLabel.setText(sys.executable)
        self.ui.pythonVersionLabel.setText(sys.version)


class MainWindow(QMainWindow):

    variableSelected = Signal(ScalarVariable, name='variableSelected')
    variableDeselected = Signal(ScalarVariable, name='variableDeselected')
    windows = []
    windowOffset = QPoint()

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        # save from garbage collection
        self.windows.append(self)

        QIcon.setThemeName('light')

        # state
        self.filename = None
        self.unzipdir = None
        self.result = None
        self.modelDescription = None
        self.variables = dict()
        self.selectedVariables = set()
        self.startValues = dict()
        self.simulationThread = None
        # self.progressDialog = None
        self.plotUpdateTimer = QTimer(self)
        self.plotUpdateTimer.timeout.connect(self.updatePlotData)
        self.curves = []

        # UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.setColorScheme(QGuiApplication.styleHints().colorScheme())

        self.showColumnActions = {}

        # use a smaller default font size on Mac and Linux
        if sys.platform in ['darwin', 'linux']:
            defaultFont = QFont()
            defaultFont.setPixelSize(11)
            QApplication.setFont(defaultFont)
            self.setStyleSheet("QWidget { font-size: 11px; }")

        self.ui.treeView.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.ui.tableView.setAttribute(Qt.WA_MacShowFocusRect, False)
        self.ui.logTreeView.setAttribute(Qt.WA_MacShowFocusRect, False)

        # set the window size to 85% of the available space
        # geo = QApplication.desktop().availableGeometry()
        # width = min(geo.width() * 0.85, 1100.0)
        # height = min(geo.height() * 0.85, 900.0)
        # self.resize(int(width), int(height))

        # hide the variables
        self.ui.dockWidget.hide()

        # toolbar
        self.stopTimeLineEdit = QLineEdit("1")
        self.stopTimeLineEdit.setToolTip("Stop time")
        self.stopTimeLineEdit.setFixedWidth(50)
        self.stopTimeValidator = QDoubleValidator(self)
        self.stopTimeValidator.setBottom(0)
        self.stopTimeLineEdit.setValidator(self.stopTimeValidator)

        self.ui.toolBar.addWidget(self.stopTimeLineEdit)

        spacer = QWidget(self)
        spacer.setFixedWidth(10)
        self.ui.toolBar.addWidget(spacer)

        self.fmiTypeComboBox = QComboBox(self)
        self.fmiTypeComboBox.addItem("Co-Simulation")
        self.fmiTypeComboBox.setToolTip("FMI type")
        self.fmiTypeComboBox.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.ui.toolBar.addWidget(self.fmiTypeComboBox)

        # disable widgets
        self.ui.actionLoadStartValues.setEnabled(False)
        self.ui.actionReload.setEnabled(False)
        self.ui.actionOpenUnzipDirectory.setEnabled(False)
        self.ui.actionShowSettings.setEnabled(False)
        self.ui.actionShowFiles.setEnabled(False)
        self.ui.actionShowDocumentation.setEnabled(False)
        self.ui.actionShowLog.setEnabled(False)
        self.ui.actionShowResults.setEnabled(False)
        self.ui.actionSimulate.setEnabled(False)
        self.ui.actionSaveResult.setEnabled(False)
        self.ui.actionSavePlottedResult.setEnabled(False)
        self.stopTimeLineEdit.setEnabled(False)
        self.fmiTypeComboBox.setEnabled(False)

        # hide the dock's title bar
        self.ui.dockWidget.setTitleBarWidget(QWidget())

        self.ui.dockWidgetContents.setMinimumWidth(500)

        self.tableModel = VariablesTableModel(self.selectedVariables, self.startValues)
        self.tableFilterModel = VariablesFilterModel()
        self.tableFilterModel.setSourceModel(self.tableModel)
        self.tableFilterModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.tableView.setModel(self.tableFilterModel)

        self.treeModel = VariablesTreeModel(self.selectedVariables, self.startValues)
        self.treeFilterModel = VariablesFilterModel()
        self.treeFilterModel.setSourceModel(self.treeModel)
        self.treeFilterModel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.ui.treeView.setModel(self.treeFilterModel)

        for i, (w, n) in enumerate(zip(VariablesModel.COLUMN_WIDTHS, VariablesModel.COLUMN_NAMES)):
            self.ui.treeView.setColumnWidth(i, w)
            self.ui.tableView.setColumnWidth(i, w)

        self.hideAllColumns()

        # populate the recent files list
        settings = QSettings()
        recent_files = settings.value("recentFiles", defaultValue=[])
        recent_files = self.removeDuplicates(recent_files)
        vbox = QVBoxLayout()

        if recent_files:
            added = set()
            for file in recent_files[:5]:
                link = QLabel('<a href="%s" style="text-decoration: none; color: #548AF7">%s</a>' % (file, os.path.basename(file)))
                link.setToolTip(file)
                link.linkActivated.connect(self.load)
                vbox.addWidget(link)
                added.add(file)

        self.ui.recentFilesGroupBox.setLayout(vbox)
        self.ui.recentFilesGroupBox.setVisible(len(recent_files) > 0)

        # settings page
        self.inputFileMenu = QMenu()
        self.inputFileMenu.addAction("New input file...", self.createInputFile)
        self.inputFileMenu.addSeparator()
        self.inputFileMenu.addAction("Show in Explorer", self.showInputFileInExplorer)
        self.inputFileMenu.addAction("Open in default application", self.openInputFile)
        self.ui.selectInputButton.setMenu(self.inputFileMenu)

        # log page
        self.log = Log(self)
        self.logFilterModel = LogMessagesFilterProxyModel(self)
        self.logFilterModel.setSourceModel(self.log)
        self.logFilterModel.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.ui.logTreeView.setModel(self.logFilterModel)
        self.ui.clearLogButton.clicked.connect(self.log.clear)

        self.log.numberOfDebugMessagesChanged.connect(lambda n: self.ui.showDebugMessagesButton.setText(str(n)))
        self.log.numberOfInfoMessagesChanged.connect(lambda n: self.ui.showInfoMessagesButton.setText(str(n)))
        self.log.numberOfWarningMessagesChanged.connect(lambda n: self.ui.showWarningMessagesButton.setText(str(n)))
        self.log.numberOfErrorMessagesChanged.connect(lambda n: self.ui.showErrorMessagesButton.setText(str(n)))

        self.ui.logFilterLineEdit.textChanged.connect(self.logFilterModel.setFilterFixedString)

        self.ui.showDebugMessagesButton.toggled.connect(self.logFilterModel.setShowDebugMessages)
        self.ui.showInfoMessagesButton.toggled.connect(self.logFilterModel.setShowInfoMessages)
        self.ui.showWarningMessagesButton.toggled.connect(self.logFilterModel.setShowWarningMessages)
        self.ui.showErrorMessagesButton.toggled.connect(self.logFilterModel.setShowErrorMessages)

        # context menu
        self.contextMenu = QMenu()
        self.actionExpandAll = self.contextMenu.addAction("Expand all")
        self.actionExpandAll.triggered.connect(self.ui.treeView.expandAll)
        self.actionCollapseAll = self.contextMenu.addAction("Collapse all")
        self.actionCollapseAll.triggered.connect(self.ui.treeView.collapseAll)
        self.contextMenu.addSeparator()
        self.actionCopyVariableName = self.contextMenu.addAction("Copy Variable Name", self.copyVariableName)
        self.actionCopyValueReference = self.contextMenu.addAction("Copy Value Reference", self.copyValueReference)
        self.contextMenu.addSeparator()
        self.actionEditTable = self.contextMenu.addAction("Edit Table", self.editTable)
        self.contextMenu.addSeparator()
        self.columnsMenu = self.contextMenu.addMenu('Columns')
        action = self.columnsMenu.addAction('Show All')
        action.triggered.connect(self.showAllColumns)
        action = self.columnsMenu.addAction('Hide All')
        action.triggered.connect(self.hideAllColumns)
        self.columnsMenu.addSeparator()
        for column in COLLAPSABLE_COLUMNS:
            action = self.columnsMenu.addAction(column)
            action.setCheckable(True)
            action.toggled.connect(lambda show, col=column: self.showColumn(col, show))
            self.showColumnActions[column] = action
        self.contextMenu.addSeparator()
        self.actionClearPlots = self.contextMenu.addAction("Clear Plots", self.clearPlots)

        # file menu
        self.ui.actionExit.triggered.connect(QApplication.closeAllWindows)
        self.ui.actionLoadStartValues.triggered.connect(self.loadStartValues)
        self.ui.actionOpenUnzipDirectory.triggered.connect(self.openUnzipDirectory)
        self.ui.actionReload.triggered.connect(lambda: self.load(self.filename))

        # tools menu
        self.ui.actionValidateFMU.triggered.connect(self.validateFMU)
        self.ui.actionCompileDarwinBinary.triggered.connect(lambda: self.compilePlatformBinary('darwin64'))
        self.ui.actionCompileLinuxBinary.triggered.connect(lambda: self.compilePlatformBinary('linux64'))
        self.ui.actionCompileWin32Binary.triggered.connect(lambda: self.compilePlatformBinary('win32'))
        self.ui.actionCompileWin64Binary.triggered.connect(lambda: self.compilePlatformBinary('win64'))
        self.ui.actionRemoveSourceCode.triggered.connect(self.removeSourceCode)
        self.ui.actionCreateJupyterNotebook.triggered.connect(self.createJupyterNotebook)
        self.ui.actionCreateCMakeProject.triggered.connect(self.createCMakeProject)
        self.ui.actionAddWindows32Remoting.triggered.connect(lambda: self.addRemotingBinaries('win64', 'win32'))
        self.ui.actionAddLinux64Remoting.triggered.connect(lambda: self.addRemotingBinaries('linux64', 'win64'))
        self.ui.actionAddCoSimulationWrapper.triggered.connect(self.addCoSimulationWrapper)

        # help menu
        self.ui.actionOpenFMI3Spec.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://fmi-standard.org/docs/3.0.2/')))
        self.ui.actionOpenFMI2Spec.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/modelica/fmi-standard/releases/download/v2.0.5/FMI-Specification-2.0.5.pdf')))
        self.ui.actionOpenFMI1SpecCS.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://fmi-standard.org/assets/releases/FMI_for_CoSimulation_v1.0.1.pdf')))
        self.ui.actionOpenFMI1SpecME.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://fmi-standard.org/assets/releases/FMI_for_ModelExchange_v1.0.1.pdf')))
        self.ui.actionOpenTestFMUs.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/modelica/fmi-cross-check/tree/master/fmus')))
        self.ui.actionOpenWebsite.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://github.com/CATIA-Systems/FMPy')))
        self.ui.actionShowReleaseNotes.triggered.connect(lambda: QDesktopServices.openUrl(QUrl('https://fmpy.readthedocs.io/en/latest/changelog/')))

        # filter menu
        self.filterMenu = QMenu()
        self.filterMenu.addAction(self.ui.actionFilterInputs)
        self.filterMenu.addAction(self.ui.actionFilterOutputs)
        self.filterMenu.addAction(self.ui.actionFilterParameters)
        self.filterMenu.addAction(self.ui.actionFilterCalculatedParameters)
        self.filterMenu.addAction(self.ui.actionFilterIndependentVariables)
        self.filterMenu.addAction(self.ui.actionFilterLocalVariables)
        self.ui.filterToolButton.setMenu(self.filterMenu)

        # status bar
        self.statusIconLabel = ClickableLabel(self)
        self.statusIconLabel.setStyleSheet("QLabel { margin-left: 5px; }")
        self.statusIconLabel.clicked.connect(lambda: self.setCurrentPage(self.ui.logPage))
        self.ui.statusBar.addPermanentWidget(self.statusIconLabel)

        self.statusTextLabel = ClickableLabel(self)
        self.statusTextLabel.setMinimumWidth(10)
        self.statusTextLabel.clicked.connect(lambda: self.setCurrentPage(self.ui.logPage))
        self.ui.statusBar.addPermanentWidget(self.statusTextLabel)

        self.ui.statusBar.addPermanentWidget(QWidget(self), 1)  # spacer

        self.simulationProgressBar = QProgressBar(self)
        self.simulationProgressBar.setFixedHeight(18)
        self.ui.statusBar.addPermanentWidget(self.simulationProgressBar)
        self.simulationProgressBar.setVisible(False)

        # connect signals and slots
        self.ui.actionNewWindow.triggered.connect(self.newWindow)
        self.ui.openButton.clicked.connect(self.open)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSaveResult.triggered.connect(self.saveResult)
        self.ui.actionSavePlottedResult.triggered.connect(lambda: self.saveResult(plotted=True))
        self.ui.actionSimulate.triggered.connect(self.startSimulation)
        self.ui.actionShowSettings.triggered.connect(lambda: self.setCurrentPage(self.ui.settingsPage))
        self.ui.actionShowFiles.triggered.connect(lambda: self.setCurrentPage(self.ui.filesPage))
        self.ui.actionShowDocumentation.triggered.connect(lambda: self.setCurrentPage(self.ui.documentationPage))
        self.ui.actionShowLog.triggered.connect(lambda: self.setCurrentPage(self.ui.logPage))
        self.ui.actionShowResults.triggered.connect(lambda: self.setCurrentPage(self.ui.resultPage))
        self.fmiTypeComboBox.currentTextChanged.connect(self.updateSimulationSettings)
        self.ui.solverComboBox.currentTextChanged.connect(self.updateSimulationSettings)
        self.variableSelected.connect(self.updatePlotLayout)
        self.variableDeselected.connect(self.updatePlotLayout)
        self.tableModel.variableSelected.connect(self.selectVariable)
        self.tableModel.variableDeselected.connect(self.deselectVariable)
        self.treeModel.variableSelected.connect(self.selectVariable)
        self.treeModel.variableDeselected.connect(self.deselectVariable)
        self.ui.filterLineEdit.textChanged.connect(self.treeFilterModel.setFilterFixedString)
        self.ui.filterLineEdit.textChanged.connect(self.tableFilterModel.setFilterFixedString)
        self.ui.filterToolButton.toggled.connect(self.treeFilterModel.setFilterByCausality)
        self.ui.filterToolButton.toggled.connect(self.tableFilterModel.setFilterByCausality)
        self.log.currentMessageChanged.connect(self.setStatusMessage)
        self.ui.selectInputButton.clicked.connect(self.selectInputFile)
        self.ui.actionShowAboutDialog.triggered.connect(self.showAboutDialog)

        if os.name == 'nt':
            self.ui.actionCreateDesktopShortcut.triggered.connect(self.createDesktopShortcut)
            self.ui.actionAddFileAssociation.triggered.connect(self.addFileAssociation)
        else:
            self.ui.actionCreateDesktopShortcut.setEnabled(False)
            self.ui.actionAddFileAssociation.setEnabled(False)

        self.ui.tableViewToolButton.toggled.connect(lambda show: self.ui.variablesStackedWidget.setCurrentWidget(self.ui.tablePage if show else self.ui.treePage))

        for model in [self.treeFilterModel, self.tableFilterModel]:
            self.ui.actionFilterInputs.triggered.connect(model.setFilterInputs)
            self.ui.actionFilterOutputs.triggered.connect(model.setFilterOutputs)
            self.ui.actionFilterParameters.triggered.connect(model.setFilterParameters)
            self.ui.actionFilterCalculatedParameters.triggered.connect(model.setFilterCalculatedParameters)
            self.ui.actionFilterIndependentVariables.triggered.connect(model.setFilterIndependentVariables)
            self.ui.actionFilterLocalVariables.triggered.connect(model.setFilterLocalVariables)

        self.ui.treeView.customContextMenuRequested.connect(self.showContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.showContextMenu)

    def newWindow(self):
        window = MainWindow()
        window.show()

    def show(self):
        super(MainWindow, self).show()
        self.move(self.frameGeometry().topLeft() + self.windowOffset)
        self.windowOffset += QPoint(20, 20)

    def closeEvent(self, event):
        self.cleanUp()
        super().closeEvent(event)

    def showContextMenu(self, point):
        """ Update and show the variables context menu """

        from .TableDialog import TableDialog

        if self.ui.variablesStackedWidget.currentWidget() == self.ui.treePage:
            currentView = self.ui.treeView
        else:
            currentView = self.ui.tableView

        self.actionExpandAll.setEnabled(currentView == self.ui.treeView)
        self.actionCollapseAll.setEnabled(currentView == self.ui.treeView)

        selected = self.getSelectedVariables()

        self.actionEditTable.setEnabled(len(selected) == 1 and TableDialog.canEdit(selected[0]))

        can_copy = len(selected) > 0

        self.actionCopyVariableName.setEnabled(can_copy)
        self.actionCopyValueReference.setEnabled(can_copy)

        self.contextMenu.exec_(currentView.mapToGlobal(point))

    def load(self, filename):

        if not self.isVisible():
            self.show()

        self.cleanUp()

        try:
            self.unzipdir = fmpy.extract(filename)
            self.modelDescription = md = read_model_description(filename)
        except Exception as e:
            QMessageBox.warning(self, "Failed to load FMU", "Failed to load %s. %s" % (filename, e))
            return

        self.filename = filename

        # show model.png
        try:
            pixmap = QPixmap(os.path.join(self.unzipdir, 'model.png'))

            # show the unscaled version in tooltip
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            pixmap.save(buffer, "PNG", quality=100)
            image = bytes(buffer.data().toBase64()).decode()
            html = '<img src="data:image/png;base64,{}">'.format(image)
            self.ui.modelImageLabel.setToolTip(html)

            # show a scaled preview in "Model Info"
            pixmap = pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.ui.modelImageLabel.setPixmap(pixmap)
        except:
            self.ui.modelImageLabel.setPixmap(QPixmap())
            self.ui.modelImageLabel.setToolTip(None)

        platforms = supported_platforms(self.filename)

        self.variables.clear()
        self.selectedVariables.clear()
        self.startValues.clear()

        for v in md.modelVariables:
            self.variables[v.name] = v
            if v.causality == 'output' and not v.dimensions:
                self.selectedVariables.add(v)

        fmi_types = []
        if md.coSimulation:
            fmi_types.append('Co-Simulation')
        if md.modelExchange:
            fmi_types.append('Model Exchange')
        if md.scheduledExecution:
            fmi_types.append('Scheduled Execution')

        experiment = md.defaultExperiment

        # toolbar
        if experiment is not None and experiment.stopTime is not None:
            self.stopTimeLineEdit.setText(str(experiment.stopTime))

        # actions
        self.ui.actionValidateFMU.setEnabled(True)

        can_compile = md.fmiVersion != '1.0' and 'c-code' in platforms

        self.ui.actionCompileDarwinBinary.setEnabled(can_compile and fmpy.system == 'darwin')
        self.ui.actionCompileLinuxBinary.setEnabled(can_compile and fmpy.system in ['linux', 'windows'])
        self.ui.actionCompileWin32Binary.setEnabled(can_compile and fmpy.system == 'windows')
        self.ui.actionCompileWin64Binary.setEnabled(can_compile and fmpy.system == 'windows')

        self.ui.actionRemoveSourceCode.setEnabled('c-code' in platforms)

        self.ui.actionCreateCMakeProject.setEnabled(can_compile)

        self.ui.actionCreateJupyterNotebook.setEnabled(True)

        self.ui.actionAddWindows32Remoting.setEnabled(md.fmiVersion == '2.0' and 'win32' in platforms and 'win64' not in platforms)
        self.ui.actionAddLinux64Remoting.setEnabled(md.fmiVersion == '2.0' and 'win64' in platforms and 'linux64' not in platforms)

        can_add_cswrapper = md.fmiVersion == '2.0' and md.coSimulation is None and md.modelExchange is not None
        self.ui.actionAddCoSimulationWrapper.setEnabled(can_add_cswrapper)

        # variables view
        self.treeModel.setModelDescription(md)
        self.tableModel.setModelDescription(md)
        self.treeFilterModel.invalidate()
        self.tableFilterModel.invalidate()
        self.ui.treeView.reset()
        self.ui.tableView.reset()

        # settings page
        self.ui.fmiVersionLabel.setText(md.fmiVersion)
        self.ui.fmiTypeLabel.setText(', '.join(fmi_types))
        self.ui.platformsLabel.setText(', '.join(platforms))
        self.ui.modelNameLabel.setText(md.modelName)
        self.ui.descriptionLabel.setText(md.description)
        self.ui.numberOfContinuousStatesLabel.setText(str(md.numberOfContinuousStates))
        self.ui.numberOfEventIndicatorsLabel.setText(str(md.numberOfEventIndicators))
        self.ui.numberOfVariablesLabel.setText(str(len(md.modelVariables)))
        self.ui.generationToolLabel.setText(md.generationTool)
        self.ui.generationDateAndTimeLabel.setText(md.generationDateAndTime)

        # relative tolerance
        if experiment is not None and experiment.tolerance is not None:
            relative_tolerance = experiment.tolerance
        else:
            relative_tolerance = 1e-6

        self.ui.relativeToleranceLineEdit.setText(str(relative_tolerance))

        # output interval
        if experiment is not None and experiment.stepSize is not None:
            output_interval = float(experiment.stepSize)
            while output_interval > 1000:
                output_interval *= 0.5
        else:
            output_interval = float(self.stopTimeLineEdit.text()) / 500

        self.ui.outputIntervalLineEdit.setText(str(output_interval))

        self.fmiTypeComboBox.clear()
        self.fmiTypeComboBox.addItems(fmi_types)

        self.updateSimulationSettings()

        self.setCurrentPage(self.ui.settingsPage)

        self.ui.dockWidget.show()

        # files page
        self.fileSystemModel = QFileSystemModel()
        self.fileSystemModel.setRootPath(self.unzipdir)
        self.ui.filesTreeView.setModel(self.fileSystemModel)
        root_index = self.fileSystemModel.index(self.unzipdir)
        self.ui.filesTreeView.setRootIndex(root_index)
        self.ui.filesTreeView.expandRecursively(root_index, 10)
        self.ui.filesTreeView.doubleClicked.connect(self.openFileInDefaultApplication)
        self.fileSystemModel.directoryLoaded.connect(self.expand)

        # documentation page
        doc_file = os.path.join(self.unzipdir, 'documentation', '_main.html' if md.fmiVersion == '1.0' else 'index.html')

        has_documentation = os.path.isfile(doc_file)

        if has_documentation:
            self.ui.webEngineView.load(QUrl.fromLocalFile(doc_file))

        self.ui.actionReload.setEnabled(True)
        self.ui.actionOpenUnzipDirectory.setEnabled(True)
        self.ui.actionShowSettings.setEnabled(True)
        self.ui.actionShowFiles.setEnabled(True)
        self.ui.actionShowDocumentation.setEnabled(has_documentation)
        self.ui.actionShowLog.setEnabled(True)
        self.ui.actionShowResults.setEnabled(False)

        if 'Co-Simulation' not in fmi_types and 'Model Exchange' not in fmi_types:
            can_sim = False
        else:
            can_sim, _ = can_simulate(platforms)

        self.ui.actionLoadStartValues.setEnabled(can_sim)
        self.ui.actionSimulate.setEnabled(can_sim)
        self.stopTimeLineEdit.setEnabled(can_sim)
        self.fmiTypeComboBox.setEnabled(can_sim and len(fmi_types) > 1)
        self.ui.settingsGroupBox.setEnabled(can_sim)

        settings = QSettings()
        recent_files = settings.value("recentFiles", defaultValue=[])
        recent_files = self.removeDuplicates([filename] + recent_files)

        # save the 10 most recent files
        settings.setValue('recentFiles', recent_files[:10])

        self.setWindowTitle("%s - FMPy" % os.path.normpath(filename))

        self.createGraphics()

    def cleanUp(self):
        if self.unzipdir:
            shutil.rmtree(self.unzipdir, ignore_errors=True)

    def open(self):

        start_dir = QDir.homePath()

        settings = QSettings()
        recent_files = settings.value("recentFiles", defaultValue=[])

        for filename in recent_files:
            dirname = os.path.dirname(filename)
            if os.path.isdir(dirname):
                start_dir = dirname
                break

        filename, _ = QFileDialog.getOpenFileName(parent=self,
                                                  caption="Open File",
                                                  dir=start_dir,
                                                  filter="FMUs (*.fmu);;All Files (*.*)")

        if filename:
            self.load(filename)

    def openFileInDefaultApplication(self, index):
        path = self.fileSystemModel.filePath(index)
        QDesktopServices.openUrl(QUrl(path))

    def setCurrentPage(self, widget):
        """ Set the current page and the actions """

        # block the signals during the update
        self.ui.actionShowSettings.blockSignals(True)
        self.ui.actionShowFiles.blockSignals(True)
        self.ui.actionShowDocumentation.blockSignals(True)
        self.ui.actionShowLog.blockSignals(True)
        self.ui.actionShowResults.blockSignals(True)

        self.ui.stackedWidget.setCurrentWidget(widget)

        # toggle the actions
        self.ui.actionShowSettings.setChecked(widget == self.ui.settingsPage)
        self.ui.actionShowFiles.setChecked(widget == self.ui.filesPage)
        self.ui.actionShowDocumentation.setChecked(widget == self.ui.documentationPage)
        self.ui.actionShowLog.setChecked(widget == self.ui.logPage)
        self.ui.actionShowResults.setChecked(widget == self.ui.resultPage)

        # un-block the signals during the update
        self.ui.actionShowSettings.blockSignals(False)
        self.ui.actionShowFiles.blockSignals(False)
        self.ui.actionShowDocumentation.blockSignals(False)
        self.ui.actionShowLog.blockSignals(False)
        self.ui.actionShowResults.blockSignals(False)

    def openUnzipDirectory(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.unzipdir))

    def expand(self):
        self.ui.filesTreeView.expandAll()
        self.ui.filesTreeView.resizeColumnToContents(0)

    def selectInputFile(self):
        start_dir = os.path.dirname(self.filename)
        filename, _ = QFileDialog.getOpenFileName(parent=self,
                                                  caption="Select Input File",
                                                  dir=start_dir,
                                                  filter="CSV Files (*.csv);;All Files (*.*)")
        if filename:
            self.ui.inputFilenameLineEdit.setText(filename)

    def createInputFile(self):
        """ Create an input file based on the input variables in the model description """

        input_variables = []

        for variable in self.modelDescription.modelVariables:
            if variable.causality == 'input':
                input_variables.append(variable)

        if len(input_variables) == 0:
            QMessageBox.warning(self,
                                "Cannot create input file",
                                "The input file cannot be created because the model has no input variables")
            return

        filename, _ = os.path.splitext(self.filename)

        filename, _ = QFileDialog.getSaveFileName(parent=self,
                                                  caption="Save Input File",
                                                  dir=filename + '_in.csv',
                                                  filter="CSV Files (*.csv);;All Files (*.*)")

        if not filename:
            return

        with open(filename, 'w') as f:

            # column names
            f.write('"time"')
            for variable in input_variables:
                f.write(',"%s"' % variable.name)
            f.write('\n')

            # example data
            f.write(','.join(['0'] * (len(input_variables) + 1)) + '\n')

        self.ui.inputFilenameLineEdit.setText(filename)

    def showInputFileInExplorer(self):
        """ Reveal the input file in the file browser """

        filename = self.ui.inputFilenameLineEdit.text()
        if not os.path.isfile(filename):
            QMessageBox.warning(self, "Cannot show input file", "The input file does not exist")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(filename)))

    def openInputFile(self):
        """ Open the input file in the default application """

        filename = self.ui.inputFilenameLineEdit.text()
        if not os.path.isfile(filename):
            QMessageBox.warning(self, "Cannot open input file", "The input file does not exist")
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(filename))

    def updateSimulationSettings(self):

        if self.fmiTypeComboBox.currentText() == 'Co-Simulation':
            self.ui.solverComboBox.setEnabled(False)
            self.ui.stepSizeLineEdit.setEnabled(False)
            self.ui.relativeToleranceLineEdit.setEnabled(True)
        else:
            self.ui.solverComboBox.setEnabled(True)
            fixed_step = self.ui.solverComboBox.currentText() == 'Fixed-step'
            self.ui.stepSizeLineEdit.setEnabled(fixed_step)
            self.ui.relativeToleranceLineEdit.setEnabled(not fixed_step)

    def selectVariable(self, variable):
        self.selectedVariables.add(variable)
        self.variableSelected.emit(variable)

    def deselectVariable(self, variable):
        self.selectedVariables.remove(variable)
        self.variableDeselected.emit(variable)

    def startSimulation(self):

        from fmpy.gui.simulation import SimulationThread

        try:
            stop_time = float(self.stopTimeLineEdit.text())
            step_size = float(self.ui.stepSizeLineEdit.text())
            relative_tolerance = float(self.ui.relativeToleranceLineEdit.text())

            if self.ui.outputIntervalRadioButton.isChecked():
                output_interval = float(self.ui.outputIntervalLineEdit.text())
            else:
                max_samples = float(self.ui.maxSamplesLineEdit.text())
                output_interval = stop_time / max_samples
        except Exception as ex:
            self.log.log('error', "Failed to start simulation: %s" % ex)
            self.ui.stackedWidget.setCurrentWidget(self.ui.logPage)
            return

        step_size = min(step_size, output_interval)

        if self.ui.solverComboBox.currentText() == 'Fixed-step':
            solver = 'Euler'
        else:
            solver = 'CVode'

        if self.ui.inputCheckBox.isChecked():

            input_variables = []
            for variable in self.modelDescription.modelVariables:
                if variable.causality == 'input':
                    input_variables.append(variable.name)
            try:
                from fmpy.util import read_csv
                filename = self.ui.inputFilenameLineEdit.text()
                input = read_csv(filename, variable_names=input_variables)
            except Exception as e:
                self.log.log('error', "Failed to load input from '%s'. %s" % (filename, e))
                return
        else:
            input = None

        output = []
        for variable in self.modelDescription.modelVariables:
            output.append(variable.name)

        fmi_type = 'CoSimulation' if self.fmiTypeComboBox.currentText() == 'Co-Simulation' else 'ModelExchange'

        self.simulationThread = SimulationThread(filename=self.unzipdir,
                                                 fmiType=fmi_type,
                                                 stopTime=stop_time,
                                                 solver=solver,
                                                 stepSize=step_size,
                                                 relativeTolerance=relative_tolerance,
                                                 outputInterval=output_interval,
                                                 startValues=self.startValues,
                                                 applyDefaultStartValues=self.ui.applyDefaultStartValuesCheckBox.isChecked(),
                                                 input=input,
                                                 output=output,
                                                 debugLogging=self.ui.debugLoggingCheckBox.isChecked(),
                                                 fmiLogging=self.ui.logFMICallsCheckBox.isChecked())

        self.ui.actionSimulate.setIcon(QIcon(':/icons/light/stop.svg'))
        self.ui.actionSimulate.setToolTip("Stop simulation")
        self.ui.actionSimulate.triggered.disconnect(self.startSimulation)
        self.ui.actionSimulate.triggered.connect(self.simulationThread.stop)

        self.simulationProgressBar.setVisible(True)

        self.simulationThread.messageChanged.connect(self.log.log)
        self.simulationThread.progressChanged.connect(self.simulationProgressBar.setValue)
        self.simulationThread.finished.connect(self.simulationFinished)

        if self.ui.clearLogOnStartButton.isChecked():
            self.log.clear()

        self.setCurrentPage(self.ui.resultPage)

        self.simulationThread.start()
        self.plotUpdateTimer.start(100)

        self.updatePlotLayout()

    def simulationFinished(self):

        # update UI
        self.ui.actionSimulate.triggered.disconnect(self.simulationThread.stop)
        self.ui.actionSimulate.triggered.connect(self.startSimulation)
        self.ui.actionSimulate.setIcon(QIcon(':/icons/dark/play.svg'))
        self.ui.actionSimulate.setToolTip("Start simulation")
        self.plotUpdateTimer.stop()
        self.simulationProgressBar.setVisible(False)
        self.ui.actionShowResults.setEnabled(True)
        self.ui.actionShowSettings.setEnabled(True)
        self.setCurrentPage(self.ui.resultPage)
        self.updatePlotLayout()

        if self.result is None:
            self.setCurrentPage(self.ui.logPage)
        else:
            self.ui.actionSaveResult.setEnabled(True)
            self.ui.actionSavePlottedResult.setEnabled(True)

        self.result = self.simulationThread.result

        self.simulationThread = None

        self.updatePlotData()

    def updatePlotData(self):

        import numpy as np

        if self.simulationThread is not None and len(self.simulationThread.rows) > 1:
            # get results from current simulation
            self.result = np.array(self.simulationThread.rows, dtype=np.dtype(self.simulationThread.cols))

        if self.result is None:
            return  # no results available yet

        time = self.result['time']

        for variable, curve in self.curves:

            if variable.name not in self.result.dtype.names:
                continue

            y = self.result[variable.name]

            if variable.type == 'Real':
                curve.setData(x=time, y=y)
            else:
                curve.setData(x=np.repeat(time, 2)[1:], y=np.repeat(y, 2)[:-1])

    def updatePlotLayout(self):

        self.ui.plotWidget.clear()

        color_scheme = QGuiApplication.styleHints().colorScheme()

        if color_scheme == Qt.ColorScheme.Dark:
            self.ui.plotWidget.setBackground('#1e1e1e')
            pg.setConfigOptions(foreground='w')
        else:
            self.ui.plotWidget.setBackground('#fbfbfb')
            pg.setConfigOptions(foreground='k')

        self.curves[:] = []

        if self.simulationThread is not None:
            stop_time = self.simulationThread.stopTime
        elif self.result is not None:
            stop_time = self.result['time'][-1]
        else:
            stop_time = 1.0

        pen = pg.mkPen('#548AF7')

        for variable in sorted(self.selectedVariables, key=lambda v: v.name):

            self.ui.plotWidget.nextRow()
            plot = self.ui.plotWidget.addPlot()

            if variable.type == 'Real':
                curve = plot.plot(pen=pen)
            else:
                if variable.type == 'Boolean':
                    plot.setYRange(0, 1, padding=0.2)
                    plot.getAxis('left').setTicks([[(0, 'false'), (1, 'true')], []])
                    curve = plot.plot(pen=pen, fillLevel=0, fillBrush=(0, 0, 255, 50), antialias=False)
                else:
                    curve = plot.plot(pen=pen, antialias=False)

            plot.setXRange(0, stop_time, padding=0.05)

            plot.setLabel('left', variable.name)
            plot.showGrid(x=True, y=True, alpha=0.25)

            # hide the auto-scale button and disable context menu and mouse interaction
            plot.hideButtons()
            plot.setMouseEnabled(False, False)
            plot.setMenuEnabled(False)

            self.curves.append((variable, curve))

        self.updatePlotData()

    def showColumn(self, name, show):
        if name in self.showColumnActions:
            self.showColumnActions[name].setChecked(show)
        i = VariablesModel.COLUMN_NAMES.index(name)
        self.ui.treeView.setColumnHidden(i, not show)
        self.ui.tableView.setColumnHidden(i, not show)

    def showAllColumns(self):
        for name in COLLAPSABLE_COLUMNS:
            self.showColumn(name, True)

    def hideAllColumns(self):
        for name in COLLAPSABLE_COLUMNS:
            self.showColumn(name, False)

    def setStatusMessage(self, level, text):

        if level in ['debug', 'info', 'warning', 'error']:
            icon = QIcon(':/icons/light/%s.svg' % level)
            self.statusIconLabel.setPixmap(icon.pixmap(QSize(16, 16)))
        else:
            self.statusIconLabel.setPixmap(QPixmap())

        self.statusTextLabel.setText(text)

    def dragEnterEvent(self, event):

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                return

        event.acceptProposedAction()

    def dropEvent(self, event):

        urls = event.mimeData().urls()

        for url in urls:
            if url == urls[0]:
                window = self
            else:
                window = MainWindow()
                
            window.load(url.toLocalFile())

    def saveResult(self, plotted=False):

        filename, _ = os.path.splitext(self.filename)

        filename, _ = QFileDialog.getSaveFileName(parent=self,
                                                  caption="Save Result",
                                                  dir=filename + '_out.csv',
                                                  filter="CSV Files (*.csv);;All Files (*.*)")

        if filename:
            from ..util import write_csv

            if plotted:
                columns = [variable.name for variable in self.selectedVariables]
            else:
                columns = None

            try:
                write_csv(filename=filename, result=self.result, columns=columns)
            except Exception as e:
                QMessageBox.critical(self, "Failed to write result", '"Failed to write "%s". %s' % (filename, e))

    def createDesktopShortcut(self):
        """ Create a desktop shortcut to start the GUI """

        import os
        from win32com.client import Dispatch
        import sys

        env = os.environ.get('CONDA_DEFAULT_ENV')

        if env is None:
            target_path = sys.executable
            root, ext = os.path.splitext(target_path)
            pythonw = root + 'w' + ext
            if os.path.isfile(pythonw):
                target_path = pythonw
            arguments = '-m fmpy.gui'
        else:
            for path in os.environ["PATH"].split(os.pathsep):
                activate = os.path.join(path, 'activate.bat')
                if os.path.isfile(activate):
                    break

            target_path = r'%windir%\System32\cmd.exe'
            arguments = '/C ""%s" %s && python -m fmpy.gui"' % (activate, env)

        file_path = os.path.dirname(__file__)
        icon = os.path.join(file_path, 'icons', 'app_icon.ico')

        desktop_locations = QStandardPaths.standardLocations(QStandardPaths.DesktopLocation)
        shortcut_path = os.path.join(desktop_locations[0], "FMPy GUI.lnk")

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.Arguments = arguments
        # shortcut.WorkingDirectory = ...
        shortcut.IconLocation = icon
        shortcut.save()

    def showAboutDialog(self):
        dialog = AboutDialog(self)
        dialog.show()

    @staticmethod
    def removeDuplicates(seq):
        """ Remove duplicates from a sequence """
        seen = set()
        seen_add = seen.add
        return [x for x in seq if not (x in seen or seen_add(x))]

    def validateFMU(self):

        from ..validation import validate_fmu

        problems = validate_fmu(self.filename)

        if problems:
            button = QMessageBox.question(self, "Validation failed", "%d problems have been found. Save validation messages?" % len(problems))
            if button == QMessageBox.Yes:
                filename, _ = os.path.splitext(self.filename)
                filename, _ = QFileDialog.getSaveFileName(parent=self,
                                                          caption="Save validation messages",
                                                          dir=filename + '_validation.txt',
                                                          filter="Text Files (*.txt);;All Files (*.*)")
                if filename:
                    with open(filename, 'w') as f:
                        f.writelines(problems)
        else:
            QMessageBox.information(self, "Validation successful", "No problems have been found.")

    def addFileAssociation(self):
        """ Associate *.fmu with the FMPy GUI """

        try:
            from winreg import HKEY_CURRENT_USER, KEY_WRITE, REG_SZ, OpenKey, CreateKey, SetValueEx, CloseKey

            env = os.environ.get('CONDA_DEFAULT_ENV_')

            if env is None:
                python = sys.executable
                root, ext = os.path.splitext(python)
                pythonw = root + 'w' + ext

                if os.path.isfile(pythonw):
                    python = pythonw

                target = '"%s" -m fmpy.gui "%%1"' % python
            else:
                # activate the conda environment
                for path in os.environ["PATH"].split(os.pathsep):
                    activate = os.path.join(path, 'activate.bat')
                    if os.path.isfile(activate):
                        break

                windir = os.environ['WINDIR']
                cmd = os.path.join(windir, 'System32', 'cmd.exe')

                target = r'%s /C ""%s" %s && python -m fmpy.gui %%1"' % (cmd, activate, env)

            key_path = r'Software\Classes\fmpy.gui\shell\open\command'

            CreateKey(HKEY_CURRENT_USER, key_path)
            key = OpenKey(HKEY_CURRENT_USER, key_path, 0, KEY_WRITE)
            SetValueEx(key, '', 0, REG_SZ, target)
            CloseKey(key)

            key_path = r'SOFTWARE\Classes\.fmu'

            CreateKey(HKEY_CURRENT_USER, key_path)
            key = OpenKey(HKEY_CURRENT_USER, key_path, 0, KEY_WRITE)
            SetValueEx(key, '', 0, REG_SZ, 'fmpy.gui')
            CloseKey(key)

            QMessageBox.information(self, "File association added", "The file association for *.fmu has been added")
        except Exception as e:
            QMessageBox.critical(self, "File association failed", "The file association for *.fmu could not be added. %s" % e)

    def copyValueReference(self):
        """ Copy the value references of the selected variables to the clipboard """

        text = '\n'.join([str(v.valueReference) for v in self.getSelectedVariables()])
        QApplication.clipboard().setText(text)

    def copyVariableName(self):
        """ Copy the names of the selected variables to the clipboard """

        text = '\n'.join([str(v.name) for v in self.getSelectedVariables()])
        QApplication.clipboard().setText(text)

    def getSelectedVariables(self):
        """ Returns a list of selected variables in the current view """

        variables = []

        if self.ui.variablesStackedWidget.currentWidget() == self.ui.treePage:
            for index in self.ui.treeView.selectionModel().selectedRows():
                sourceIndex = self.treeFilterModel.mapToSource(index)
                treeItem = sourceIndex.internalPointer()
                if treeItem.variable is not None:
                    variables.append(treeItem.variable)
        else:
            for index in self.ui.tableView.selectionModel().selectedRows():
                sourceIndex = self.tableFilterModel.mapToSource(index)
                variable = sourceIndex.internalPointer()
                variables.append(variable)

        return variables

    def clearPlots(self):
        """ Clear all plots """
        self.selectedVariables.clear()
        self.updatePlotLayout()

    def createGraphics(self):
        """ Create the graphical representation of the FMU's inputs and outputs """

        def variableColor(variable):
            if variable.type.startswith(('Float', 'Real')):
                return QColor.fromRgb(26, 77, 179)
            elif variable.type.startswith(('Enumeration', 'Int', 'UInt', 'Clock')):
                return QColor.fromRgb(179, 77, 26)
            elif variable.type == 'Boolean':
                return QColor.fromRgb(255, 0, 255)
            elif variable.type == 'String':
                return QColor.fromRgb(26, 114, 16)
            elif variable.type == 'Binary':
                return QColor.fromRgb(81, 81, 81)
            else:
                return QColor.fromRgb(0, 0, 0)

        inputVariables = []
        outputVariables = []
        maxInputLabelWidth = 0
        maxOutputLabelWidth = 0

        textItem = QGraphicsTextItem()
        fontMetrics = QFontMetricsF(textItem.font())

        for variable in self.modelDescription.modelVariables:
            if variable.causality == 'input':
                inputVariables.append(variable)
            elif variable.causality == 'output':
                outputVariables.append(variable)

        for variable in inputVariables:
            maxInputLabelWidth = max(maxInputLabelWidth, fontMetrics.horizontalAdvance(variable.name))

        for variable in outputVariables:
            maxOutputLabelWidth = max(maxOutputLabelWidth, fontMetrics.horizontalAdvance(variable.name))

        from math import floor

        scene = QGraphicsScene()
        self.ui.graphicsView.setScene(scene)
        group = QGraphicsItemGroup()
        scene.addItem(group)
        lh = 15  # line height

        w = max(150., maxInputLabelWidth + maxOutputLabelWidth + 20)
        h = max(50., 10 + lh * max(len(inputVariables), len(outputVariables)))

        block = QGraphicsRectItem(0, 0, w, h, group)

        if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            textColor = QColor.fromRgb(255, 255, 255)
        else:
            textColor = QColor.fromRgb(0, 0, 0)

        block.setPen(textColor)

        pen = QPen()
        pen.setWidthF(1)

        font = QFont()
        font.setPixelSize(10)

        # inputs
        y = floor((h - len(inputVariables) * lh) / 2 - 2)

        for variable in inputVariables:

            text = QGraphicsTextItem(variable.name)
            group.addToGroup(text)
            text.setFont(font)
            text.setX(3)
            text.setY(y)

            polygon = QPolygonF([QPointF(-8, y + 7.5), QPointF(-1, y + 11), QPointF(-8, y + 14.5)])

            path = QPainterPath()
            path.addPolygon(polygon)
            path.closeSubpath()
            contour = QGraphicsPathItem(path, group)
            contour.setPen(QPen(Qt.NoPen))
            contour.setBrush(variableColor(variable))
            pen = QPen()
            pen.setColor(variableColor(variable))
            pen.setJoinStyle(Qt.MiterJoin)
            contour.setPen(pen)

            y += lh

        # outputs
        y = floor((h - len(outputVariables) * lh) / 2 - 2)

        for variable in outputVariables:

            text = QGraphicsTextItem(variable.name)
            group.addToGroup(text)
            text.setFont(font)
            text.setX(w - 3 - text.boundingRect().width())
            text.setY(y)

            polygon = QPolygonF([QPointF(w + 1, y + 7.5), QPointF(w + 8, y + 11), QPointF(w + 1, y + 14.5)])

            path = QPainterPath()
            path.addPolygon(polygon)
            path.closeSubpath()
            contour = QGraphicsPathItem(path, group)
            contour.setPen(QPen(Qt.NoPen))
            contour.setBrush(variableColor(variable))
            pen = QPen()
            pen.setColor(variableColor(variable))
            pen.setJoinStyle(Qt.MiterJoin)
            contour.setPen(pen)

            y += lh

    def loadStartValues(self):
        from ..util import get_start_values

        start_values = get_start_values(self.filename)

        self.startValues.update(start_values)

        self.ui.treeView.reset()
        self.ui.tableView.reset()

    def editTable(self):
        """ Open the table dialog """

        from .TableDialog import TableDialog

        variables = self.getSelectedVariables()

        if len(variables) == 1:
            start_values = self.startValues.copy()
            dialog = TableDialog(modelVariables=self.modelDescription.modelVariables,
                                 variable=variables[0],
                                 startValues=start_values)

            if dialog.exec_() == QDialog.Accepted:
                self.startValues.clear()
                self.startValues.update(start_values)

    def compilePlatformBinary(self, target_platform):
        """ Compile the platform binary """

        from ..util import compile_platform_binary

        platforms = supported_platforms(self.filename)

        if target_platform in platforms:
            button = QMessageBox.question(self, "Platform binary already exists",
                                          f'The FMU already contains a binary for the platform "{target_platform}".'
                                          ' Do you want to compile and overwrite the existing binary?')
            if button == QMessageBox.No:
                return

        if self.modelDescription.fmiVersion == '3.0':

            platform_map = {
                'darwin64': 'x86_64-darwin',
                'linux64': 'x86_64-linux',
                'win32': 'x86-windows',
                'win64': 'x86_64-windows',
            }
            
            target_platform = platform_map[target_platform]

        try:
            compile_platform_binary(self.filename, target_platform=target_platform)
        except Exception as e:
            QMessageBox.critical(self, "Failed to compile platform binaries", str(e))
            return

        self.load(self.filename)

    def removeSourceCode(self):

        button = QMessageBox.question(self, "Remove Source Code?", "Do you want to remove the source code from the FMU?\nThis action cannot be undone.")

        if button == QMessageBox.Yes:
            remove_source_code(self.filename)
            self.load(self.filename)

    def createJupyterNotebook(self):
        """ Create a Jupyter Notebook to simulate the FMU """

        from fmpy.util import create_jupyter_notebook

        filename, ext = os.path.splitext(self.filename)

        filename, _ = QFileDialog.getSaveFileName(
            parent=self,
            dir=f'{filename}.ipynb',
            filter='Jupyter Notebooks (*.ipynb);;All Files (*)'
        )

        if filename:
            try:
                create_jupyter_notebook(self.filename, filename)
            except Exception as e:
                QMessageBox.critical(self, "Failed to create Jupyter Notebook", str(e))
                return

            if QMessageBox.question(self, "Open Jupyter Notebook?", f"Start Jupyter and open {filename}?") == QMessageBox.Yes:

                from subprocess import Popen, CREATE_NEW_CONSOLE

                try:
                    Popen(['jupyter', 'notebook', filename], creationflags=CREATE_NEW_CONSOLE)
                except Exception as e:
                    QMessageBox.critical(self, "Failed to start Jupyter", str(e))

    def createCMakeProject(self):
        """ Create a CMake project from a C code FMU """

        from fmpy.util import create_cmake_project

        project_dir = QFileDialog.getExistingDirectory(
            parent=self,
            caption='Select CMake Project Folder',
            dir=os.path.dirname(self.filename))

        if project_dir:
            create_cmake_project(self.filename, project_dir)


    def addRemotingBinaries(self, host_platform, remote_platform):

        from ..util import add_remoting

        try:
            add_remoting(self.filename, host_platform, remote_platform)
        except Exception as e:
            QMessageBox.warning(self, "Failed to add Remoting Binaries",
                                f"Failed to add remoting binaries to {self.filename}. {e}")

        self.load(self.filename)


    def addCoSimulationWrapper(self):
        """ Add the Co-Simulation Wrapper to the FMU """

        from ..cswrapper import add_cswrapper

        try:
            add_cswrapper(self.filename)
        except Exception as e:
            QMessageBox.warning(self, "Failed to add Co-Simulation Wrapper",
                                "Failed to add Co-Simulation Wrapper %s. %s" % (self.filename, e))

        self.load(self.filename)


    def setColorScheme(self, colorScheme: Qt.ColorScheme):

        theme = 'dark' if colorScheme == Qt.ColorScheme.Dark else 'light'

        self.ui.actionOpen.setIcon(QIcon(f':/icons/{theme}/folder-open.svg'))
        self.ui.actionReload.setIcon(QIcon(f':/icons/{theme}/arrow-clockwise.svg'))
        self.ui.actionShowSettings.setIcon(QIcon(f':/icons/{theme}/gear.svg'))
        self.ui.actionShowFiles.setIcon(QIcon(f':/icons/{theme}/file-earmark-zip.svg'))
        self.ui.actionShowDocumentation.setIcon(QIcon(f':/icons/{theme}/book.svg'))
        self.ui.actionShowLog.setIcon(QIcon(f':/icons/{theme}/list-task.svg'))
        self.ui.actionShowResults.setIcon(QIcon(f':/icons/{theme}/graph.svg'))

        self.ui.filterToolButton.setIcon(QIcon(f':/icons/{theme}/filter.svg'))
        self.ui.tableViewToolButton.setIcon(QIcon(f':/icons/{theme}/list.svg'))
