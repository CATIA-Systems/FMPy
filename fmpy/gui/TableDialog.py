from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QDialog, QHeaderView
import pyqtgraph as pg
import numpy as np

from fmpy.gui.generated.TableDialog import Ui_TableDialog

pg.setConfigOptions(background='w', foreground='k', antialias=True)


class TableModel(QAbstractTableModel):

    def __init__(self, size, data, startValues, parent=None):
        super(TableModel, self).__init__(parent)
        self.size = size
        self.data = data
        self.startValues = startValues
        self.boldFont = QFont()
        self.boldFont.setBold(True)

    def rowCount(self, index=QModelIndex()):
        return self.size[0]

    def columnCount(self, index=QModelIndex()):
        if len(self.size) == 1:
            return 1
        else:
            return self.size[1]

    def headerData(self, section, orientation, role):

        if role == Qt.DisplayRole:

            if orientation == Qt.Horizontal:
                if len(self.size) > 1:
                    return section + 1
            else:
                return section + 1

        return None

    def flags(self, index):
        flags = super(TableModel, self).flags(index) | Qt.ItemIsEditable
        return flags

    def data(self, index, role=Qt.DisplayRole):

        if not index.isValid():
            return None

        subs = self.ind2sub(index)
        sv = self.data[subs]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if sv.name in self.startValues:
                return self.startValues[sv.name]
            else:
                return sv.start

        elif role == Qt.TextAlignmentRole:
            return Qt.AlignRight | Qt.AlignVCenter

        elif role == Qt.FontRole and sv.name in self.startValues:
            return self.boldFont

        return None

    def setData(self, index, value, role):
        subs = self.ind2sub(index)
        sv = self.data[subs]

        if value:
            self.startValues[sv.name] = value
        else:
            self.startValues.pop(sv.name, None)

        self.dataChanged.emit(index, index)

        return True

    def ind2sub(self, index):
        """ Convert index to subscripts """

        if len(self.size) == 1:
            return index.row(),
        else:
            return index.row(), index.column()


class TableDialog(QDialog):
    """ A dialog to edit 1-d and 2-d array variables """

    def __init__(self, modelVariables, variable, startValues, parent=None):
        """
        Parameters:
            modelVariables: list of variables from the model description
            variable:       the (array) variable to be edited
            startValues:    dictionary of modified start values
        """

        super(TableDialog, self).__init__(parent)

        self.modelVariables = modelVariables
        self.startValues = startValues

        self.ui = Ui_TableDialog()
        self.ui.setupUi(self)

        # hide the question mark button
        flags = self.windowFlags()
        flags &= ~Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)

        verticalHeader = self.ui.tableView.verticalHeader()
        verticalHeader.setSectionResizeMode(QHeaderView.Fixed)
        verticalHeader.setDefaultSectionSize(24)

        self.data = dict()
        size = None

        variable_name = variable.name
        i = variable_name.rfind('[')
        variable_name = variable_name[:i]

        for sv in self.modelVariables:
            if sv.name.startswith(variable_name):
                i = sv.name.rfind('[')
                subs = sv.name[i+1:-1]
                subs = subs.split(',')
                subs = list(map(lambda s: int(s) - 1, subs))
                if size is None:
                    size = subs
                else:
                    for i, index in enumerate(subs):
                        size[i] = max(size[i], index + 1)

                self.data[tuple(subs)] = sv

        self.size = size

        self.setWindowTitle(variable_name + '[' + ','.join(map(str, size)) + ']')
        self.setWindowIcon(QIcon(':/icons/%s.png' % variable.type.lower()))

        self.model = TableModel(size, self.data, self.startValues)
        self.ui.tableView.setModel(self.model)

        self.ui.tableView.resizeColumnsToContents()

        self.updatePlot()

        self.ui.splitter.setSizes([450, 450])

        if len(size) < 2:
            self.ui.plotSettingsWidget.hide()

        self.model.dataChanged.connect(self.updatePlot)

        self.ui.plotColumnsRadioButton.toggled.connect(self.updatePlot)
        self.ui.firstColumnAsXAxisCheckBox.toggled.connect(self.updatePlot)
        self.ui.firstRowAsXAxisCheckBox.toggled.connect(self.updatePlot)

    @staticmethod
    def canEdit(variable):
        """ Determine whether the variable can be edited """

        if variable.type not in ['Real', 'Integer', 'Enumeration']:
            return False

        try:
            subs = TableDialog.subscripts(variable.name)
            return 0 < len(subs) <= 2
        except:
            return False

        return False

    @staticmethod
    def subscripts(name):
        """ Get the subscripts from a variable name """

        i = name.rfind('[')
        subs = name[i + 1:-1]
        subs = subs.split(',')
        return list(map(lambda s: int(s) - 1, subs))

    def updatePlot(self):

        data = np.zeros(self.size)

        for subs, variable in self.data.items():
            if variable.name in self.startValues:
                data[subs] = float(self.startValues[variable.name])
            else:
                if variable.start:
                    data[subs] = float(variable.start)
                else:
                    data[subs] = np.nan

        self.ui.graphicsView.clear()
        plot = self.ui.graphicsView.addPlot()
        plot.showGrid(x=True, y=True, alpha=0.25)

        if len(self.size) == 1:
            plot.plot(y=data, pen='b', symbolPen=None, symbolBrush='b', symbolSize=5)
        else:
            vb = self.ui.graphicsView.addViewBox()
            vb.setMaximumWidth(100)
            legend = pg.LegendItem()
            legend.setParentItem(vb)
            # Anchor the upper-left corner of the legend to the upper-left corner of its parent
            legend.anchor((0, 0), (0, 0))

            if self.ui.plotColumnsRadioButton.isChecked():

                if self.ui.firstColumnAsXAxisCheckBox.isChecked():
                    for i in range(1, min(data.shape[1], 20)):
                        color = pg.intColor(i, hues=data.shape[1] - 1, maxValue=200)
                        line = plot.plot(x=data[:, 0], y=data[:, i], pen=color, symbolPen=None, symbolBrush=color, symbolSize=5)
                        legend.addItem(line, 'Column %d' % (i + 1))

                else:
                    for i in range(data.shape[1]):
                        color = pg.intColor(i, hues=data.shape[1], maxValue=200)
                        line = plot.plot(y=data[:, i], pen=color, symbolPen=None, symbolBrush=color, symbolSize=5)
                        legend.addItem(line, 'Column %d' % (i + 1))

            else:

                n = min(data.shape[0], 30)

                if self.ui.firstRowAsXAxisCheckBox.isChecked():

                    for i in range(1, n):
                        color = pg.intColor(i, hues=n, maxValue=200)
                        line = plot.plot(x=data[0, :], y=data[i, :], pen=color, symbolPen=None, symbolBrush=color, symbolSize=5)
                        legend.addItem(line, 'Row %d' % (i + 1))
                else:
                    for i in range(n):
                        color = pg.intColor(i, hues=n, maxValue=200)
                        line = plot.plot(y=data[i, :], pen=color, symbolPen=None, symbolBrush=color, symbolSize=5)
                        legend.addItem(line, 'Row %d' % (i + 1))
