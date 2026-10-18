import re
from html import escape
from PySide6.QtCore import Qt, QObject, QTimer
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

        # throttle the HTML updates to avoid rebuilding the page for every message
        self.updateHtmlTimer = QTimer(self)
        self.updateHtmlTimer.setSingleShot(True)
        self.updateHtmlTimer.setInterval(100)
        self.updateHtmlTimer.timeout.connect(self.updateHtml)

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

        if not self.updateHtmlTimer.isActive():
            self.updateHtmlTimer.start()

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
body {
    background-color: $background;
}

pre {
    font-size: 13px;
    line-height: 130%;
    margin: 0em;
}

pre.debug {
    color: $grey;
}

pre.info {
    color: $blue;
}

pre.warning {
    color: $yellow;
}

pre.error {
    color: $red;
}
</style>
</head>
<body>
''').substitute(**colors)

        symbols = {
            "debug": "\u2022",    # bullet
            "info": "\u2139",     # information source
            "warning": "\u26a0",  # warning sign
            "error": "\u2716",    # heavy multiplication x
        }

        for level, text in self.messages:

            if self.pattern.lower() not in text.lower():
                continue

            if (level == "debug" and self.showDebugMessages or
                level == "info" and self.showInfoMessages or
                level == "warning" and self.showWarningMessages or
                level == "error" and self.showErrorMessages):
                html += f'<pre class="{level}">{symbols[level]} {escape(text)}</pre>\n'

        html += "</body></html>"

        self.htmlChanged.emit(html)
