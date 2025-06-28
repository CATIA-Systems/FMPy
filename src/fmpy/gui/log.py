import re
from PySide6.QtCore import Qt, QObject
from PySide6.QtCore import Signal
from PySide6.QtGui import QGuiApplication
from string import Template
from typing import Literal, get_args


class Log(QObject):

    Severity = Literal['debug', 'info', 'warning', 'error']

    currentMessageChanged = Signal(str, str)
    htmlChanged = Signal(str)
    numberOfDebugMessagesChanged = Signal(int)
    numberOfInfoMessagesChanged = Signal(int)
    numberOfWarningMessagesChanged = Signal(int)
    numberOfErrorMessagesChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pattern = ""

        self.currentLevel: Log.Severity = 'debug'

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
    def severity(level: Severity):
        return get_args(Log.Severity).index(level)

    def clear(self):
        self.currentLevel = 'debug'
        self.messages[:] = []
        self.updateHtml()

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

        self.updateHtml()

    def setShowDebugMessages(self, show):
        self.showDebugMessages = show
        self.updateHtml()

    def setShowInfoMessages(self, show):
        self.showInfoMessages = show
        self.updateHtml()

    def setShowWarningMessages(self, show):
        self.showWarningMessages = show
        self.updateHtml()

    def setShowErrorMessages(self, show):
        self.showErrorMessages = show
        self.updateHtml()

    def setFilterString(self, pattern: str):
        self.pattern = pattern
        self.updateHtml()

    def updateHtml(self):

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

            if self.pattern.lower() not in text.lower():
                continue

            if (level == "debug" and self.showDebugMessages or
                level == "info" and self.showInfoMessages or
                level == "warning" and self.showWarningMessages or
                level == "error" and self.showErrorMessages):
                html += f'<pre class="{level}">{text}</pre>\n'

        html += "</body></html>"

        self.htmlChanged.emit(html)
