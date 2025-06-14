from PySide6.QtWidgets import QDialog, QWidget
from fmpy.gui.generated.GenerateFMUDialog import Ui_GenerateFMUDialog


class GenerateFMUDialog(QDialog):

    def __init__(self, parent: QWidget | None = None):

        super().__init__(parent)

        self.ui = Ui_GenerateFMUDialog()
        self.ui.setupUi(self)


