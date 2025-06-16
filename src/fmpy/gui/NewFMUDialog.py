import os

from PySide6.QtWidgets import QDialog, QWidget, QFileDialog
from fmpy.gui.generated.NewFMUDialog import Ui_NewFMUDialog


class NewFMUDialog(QDialog):

    def __init__(self, parent: QWidget | None = None):

        super().__init__(parent)

        self.ui = Ui_NewFMUDialog()
        self.ui.setupUi(self)
        self.ui.selectFilenameButton.clicked.connect(self.selectFilename)

    def selectFilename(self):
        filename, _ = QFileDialog.getSaveFileName(parent=self,
                                                  caption="Select Filename",
                                                  dir=self.ui.filenameLineEdit.text(),
                                                  filter="FMUs (*.fmu)")
        if filename:
            self.ui.filenameLineEdit.setText(filename)
