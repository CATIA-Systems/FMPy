from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel, QObject
from PySide6.QtGui import QIcon, QGuiApplication
from PySide6.QtCore import Signal
import re


class Log2(QObject):

    currentMessageChanged = Signal(str, str)
    textChanged = Signal(str)
    numberOfDebugMessagesChanged = Signal(int)
    numberOfInfoMessagesChanged = Signal(int)
    numberOfWarningMessagesChanged = Signal(int)
    numberOfErrorMessagesChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filter = ""

        self.currentLevel = 'debug'

        self.messages = []

        self.showDebugMessages = False
        self.showInfoMessages = True
        self.showWarningMessages = True
        self.showErrorMessages = True

        self.numberOfDebugMessages = 0
        self.numberOfInfoMessages = 0
        self.numberOfWarningMessages = 0
        self.numberOfErrorMessages = 0

    @staticmethod
    def severity(level):
        return ['debug', 'info', 'warning', 'error'].index(level)

    def clear(self):
        self.currentLevel = 'debug'
        self.messages[:] = []
        self.updateText()

        self.currentMessageChanged.emit('', '')

        self.numberOfDebugMessages = 0
        self.numberOfInfoMessages = 0
        self.numberOfWarningMessages = 0
        self.numberOfErrorMessages = 0

        self.numberOfDebugMessagesChanged.emit(self.numberOfDebugMessages)
        self.numberOfInfoMessagesChanged.emit(self.numberOfInfoMessages)
        self.numberOfWarningMessagesChanged.emit(self.numberOfWarningMessages)
        self.numberOfErrorMessagesChanged.emit(self.numberOfErrorMessages)

    def logMessage(self, level: str, text: str):

        self.messages.append((level, text))

        if self.severity(level) >= self.severity(self.currentLevel):
            self.currentLevel = level
            stripped = re.sub(r'\s+', ' ', text).strip()
            self.currentMessageChanged.emit(level, stripped)

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

        self.updateText()

    def setShowDebugMessages(self, show):
        self.showDebugMessages = show
        self.updateText()

    def setShowInfoMessages(self, show):
        self.showInfoMessages = show
        self.updateText()

    def setShowWarningMessages(self, show):
        self.showWarningMessages = show
        self.updateText()

    def setShowErrorMessages(self, show):
        self.showErrorMessages = show
        self.updateText()

    def setFilterFixedString(self, filter: str):
        self.filter = filter
        self.updateText()

    def updateText(self):

        if QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark:
            colors = {
                "background": "#171717",
                "grey": "#cdcdcd",
                "blue": "#a5ccfc",
                "yellow": "#fceca5",
                "red": "#fcb1a5",
            }
        else:
            colors = {
                "background": "#ffffff",
                "grey": "#707070",
                "blue": "#2f7fe1",
                "yellow": "#b19c16",
                "red": "#a9493a",
            }

        from string import Template

        html = Template('''
<html>
<head>
<style>
::-webkit-scrollbar {
  width: 10px;
  height: 10px;
}

::-webkit-scrollbar-thumb {
  border-radius: 10px;
  background: #A0A0A4;
}

::-webkit-scrollbar-thumb:hover {
  background: #A9A9AD;
}

::-webkit-scrollbar-corner {
  background-color: transparent;
}

body {
    background-color: $background;
}

pre {
    font-size: 13px;
    line-height: 130%;
    background-repeat: no-repeat;
    background-size: 1.2em 1.2em;
    padding-left: 1.5em;
    margin: 0em;
}

pre.debug {
    background-image: url('qrc:/icons/light/debug.svg');
    color: $grey;
}

pre.info {
    background-image: url('qrc:/icons/light/info.svg');
    color: $blue;
}

pre.warning {
    background-image: url('qrc:/icons/light/warning.svg');
    color: $yellow;
}

pre.error {
    background-image: url('qrc:/icons/light/error.svg');
    color: $red;
}
</style>
</head>
<body>
''').substitute(**colors)

        for level, text in self.messages:

            if self.filter.lower() not in text.lower():
                continue

            # from random import randint
            # levels = ['debug', 'info', 'warning', 'error']
            #
            # level = levels[randint(0,3)]

            if (level == "debug" and self.showDebugMessages or
                level == "info" and self.showInfoMessages or
                level == "warning" and self.showWarningMessages or
                level == "error" and self.showErrorMessages):
                html += f'<pre class="{level}">{text}</pre>\n'

        html += "</body></html>"

        self.textChanged.emit(html)

        # print(html)


class Log(QAbstractTableModel):

    textChanged = Signal(str)

    currentMessageChanged = Signal(str, str)
    numberOfDebugMessagesChanged = Signal(int)
    numberOfInfoMessagesChanged = Signal(int)
    numberOfWarningMessagesChanged = Signal(int)
    numberOfErrorMessagesChanged = Signal(int)

    @staticmethod
    def severity(level):
        return ['debug', 'info', 'warning', 'error'].index(level)

    def __init__(self, parent=None):
        super().__init__(parent)
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
        simplified = re.sub(r'\s+', ' ', text).strip()
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

        text = "\n".join(m[2] for m in self.messages)

        self.textChanged.emit(text)

    def data(self, index, role):

        level, simplified, text = self.messages[index.row()]

        if role == Qt.DisplayRole:
            return simplified
        elif role == Qt.ToolTipRole:
            return text
        elif role == Qt.DecorationRole:
            return QIcon(':/icons/light/%s.svg' % level)

        return None


class LogMessagesFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)
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
