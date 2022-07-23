import sys
from pathlib import Path

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QFileDialog
from modelica_fmi.FMUImportDialog import FMUImportDialog
import os
import sys
import ctypes
import platform

if __name__ == '__main__':

    workdir = Path(__file__).parent.absolute()

    app = QApplication(sys.argv)

    # fileName, _ = QFileDialog.getOpenFileName(caption="Select FMU",
    #                                           directory=str(workdir),
    #                                           filter="Functional Mock-up Units (*.fmu)")

    if os.name == 'nt' and int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

    QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

    dialog = FMUImportDialog()

    sys.exit(dialog.exec_())
