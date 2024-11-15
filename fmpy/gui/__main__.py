""" Entry point for the graphical user interface """

if __name__ == '__main__':

    import os
    import sys
    import ctypes
    import platform
    from PySide6 import QtCore
    from PySide6.QtWidgets import QApplication
    from fmpy.gui.MainWindow import MainWindow

    if os.name == 'nt' and int(platform.release()) >= 8:
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

    # QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    # QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    for i, v in enumerate(sys.argv[1:]):
        if i > 0:
            window = MainWindow()
            window.show()
        window.load(v)

    sys.exit(app.exec())
