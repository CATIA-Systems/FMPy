from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont


class Log(QAbstractTableModel):

    currentMessageChanged = pyqtSignal(str, str)

    @staticmethod
    def severity(level):
        return ['debug', 'info', 'warning', 'error'].index(level)

    def __init__(self, parent=None):
        super(QAbstractTableModel, self).__init__(parent)
        self.messages = []
        self.currentLevel = 'debug'

    def clear(self):
        self.beginResetModel()
        self.currentLevel = 'debug'
        self.messages.clear()
        self.endResetModel()

    def columnCount(self, parent):
        return 1

    def rowCount(self, parent):
        return len(self.messages)

    def log(self, level, text):
        import re

        last = len(self.messages)
        simplified = re.sub('\s+', ' ', text).strip()
        self.beginInsertRows(QModelIndex(), last, last + 1)
        self.messages.append((level, simplified, text))
        self.endInsertRows()

        if self.severity(level) >= self.severity(self.currentLevel):
            self.currentLevel = level
            self.currentMessageChanged.emit(level, simplified)

    def data(self, index, role):

        level, simplified, text = self.messages[index.row()]

        if role == Qt.DisplayRole:
            return simplified
        elif role == Qt.ToolTipRole:
            return text
        elif role == Qt.DecorationRole:
            return QPixmap(':/icons/%s-16x16.png' % level)

        return None
