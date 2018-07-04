from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal, QSortFilterProxyModel
from PyQt5.QtGui import QPixmap


class Log(QAbstractTableModel):

    currentMessageChanged = pyqtSignal(str, str)
    numberOfDebugMessagesChanged = pyqtSignal(int)
    numberOfInfoMessagesChanged = pyqtSignal(int)
    numberOfWarningMessagesChanged = pyqtSignal(int)
    numberOfErrorMessagesChanged = pyqtSignal(int)

    @staticmethod
    def severity(level):
        return ['debug', 'info', 'warning', 'error'].index(level)

    def __init__(self, parent=None):
        super(QAbstractTableModel, self).__init__(parent)
        self.messages = []
        self.currentLevel = 'debug'
        self.numberOfDebugMessages = 0
        self.numberOfInfoMessages = 0
        self.numberOfWarningMessages = 0
        self.numberOfErrorMessages = 0

    def clear(self):
        self.beginResetModel()
        self.currentLevel = 'debug'
        self.messages[:] = []
        self.endResetModel()

        self.currentMessageChanged.emit('', '')

        self.numberOfDebugMessages = 0
        self.numberOfInfoMessages = 0
        self.numberOfWarningMessages = 0
        self.numberOfErrorMessages = 0

        self.numberOfDebugMessagesChanged.emit(self.numberOfDebugMessages)
        self.numberOfInfoMessagesChanged.emit(self.numberOfInfoMessages)
        self.numberOfWarningMessagesChanged.emit(self.numberOfWarningMessages)
        self.numberOfErrorMessagesChanged.emit(self.numberOfErrorMessages)

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        return len(self.messages)

    def log(self, level, text):
        import re

        last = len(self.messages)
        simplified = re.sub('\s+', ' ', text).strip()
        self.beginInsertRows(QModelIndex(), last, last)
        self.messages.append((level, simplified, text))
        self.endInsertRows()

        if self.severity(level) >= self.severity(self.currentLevel):
            self.currentLevel = level
            self.currentMessageChanged.emit(level, simplified)

        if level == 'debug':
            self.numberOfDebugMessages += 1
            self.numberOfDebugMessagesChanged.emit(self.numberOfDebugMessages)
        elif level == 'info':
            self.numberOfInfoMessages += 1
            self.numberOfInfoMessagesChanged.emit(self.numberOfInfoMessages)
        elif level == 'warning':
            self.numberOfWarningMessages += 1
            self.numberOfWarningMessagesChanged.emit(self.numberOfWarningMessages)
        elif level == 'error':
            self.numberOfErrorMessages += 1
            self.numberOfErrorMessagesChanged.emit(self.numberOfErrorMessages)

    def data(self, index, role):

        level, simplified, text = self.messages[index.row()]

        if role == Qt.DisplayRole:
            return simplified
        elif role == Qt.ToolTipRole:
            return text
        elif role == Qt.DecorationRole:
            return QPixmap(':/icons/%s-16x16.png' % level)

        return None


class LogMessagesFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super(QSortFilterProxyModel, self).__init__(parent)
        self.showDebugMessages = False
        self.showInfoMessages = True
        self.showWarningMessages = True
        self.showErrorMessages = True

    def filterAcceptsRow(self, source_row, source_parent):

        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)

        if index.isValid():

            level, _, _ = model.messages[source_row]

            if level == 'debug' and not self.showDebugMessages:
                return False
            elif level == 'info' and not self.showInfoMessages:
                return False
            elif level == 'warning' and not self.showWarningMessages:
                return False
            elif level == 'error' and not  self.showErrorMessages:
                return False

        return QSortFilterProxyModel.filterAcceptsRow(self, source_row, source_parent)

    def setShowDebugMessages(self, show):
        self.showDebugMessages = show
        self.invalidateFilter()

    def setShowInfoMessages(self, show):
        self.showInfoMessages = show
        self.invalidateFilter()

    def setShowWarningMessages(self, show):
        self.showWarningMessages = show
        self.invalidateFilter()

    def setShowErrorMessages(self, show):
        self.showErrorMessages = show
        self.invalidateFilter()
