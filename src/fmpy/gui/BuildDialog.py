import os

from PySide6.QtWidgets import QDialog, QWidget, QFileDialog, QDialogButtonBox

from fmpy.gui.generated.BuildDialog import Ui_BuildDialog


class BuildDialog(QDialog):

    def __init__(self, parent: QWidget | None = None):

        super().__init__(parent)

        self.ui = Ui_BuildDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText("Build")
        self.ui.selectBuildDirectoryToolButton.clicked.connect(self.selectBuildDirectory)
        self.ui.compileWithWslCheckBox.setEnabled(os.name == 'nt')

    def selectBuildDirectory(self):
        path = QFileDialog.getExistingDirectory(parent=self,
                                                  caption="Select Build Directory",
                                                  dir=self.ui.buildDirectoryLineEdit.text())
        if path:
            self.ui.buildDirectoryLineEdit.setText(path)
