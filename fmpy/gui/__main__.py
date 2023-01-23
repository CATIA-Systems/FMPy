""" Entry point for the graphical user interface """

if __name__ == '__main__':

    # from PySide6.QtWidgets import QApplication, QWidget
    #
    # # Only needed for access to command line arguments
    # import sys
    #
    # # You need one (and only one) QApplication instance per application.
    # # Pass in sys.argv to allow command line arguments for your app.
    # # If you know you won't use command line arguments QApplication([]) works too.
    # app = QApplication(sys.argv)
    #
    # # Create a Qt widget, which will be our window.
    # window = QWidget()
    # window.show()  # IMPORTANT!!!!! Windows are hidden by default.
    #
    # # Start the event loop.
    # app.exec_()

    import sys
    from PySide6.QtWidgets import QApplication, QPushButton, QStyleFactory
    from PySide6.QtWebEngineWidgets import QWebEngineView
    from PySide6 import QUrl

    app = QApplication(sys.argv)

    # QApplication::setStyle(QStyleFactory::create("Fusion"));

    # ("Windows", "WindowsXP", "WindowsVista", "Fusion")
    app.setStyle(QStyleFactory.create('Fusion'))

    view = QWebEngineView()
    view.load(QUrl("http://qt-project.org/"))
    view.show()

    # window = QPushButton("Push Me")
    # window.show()

    app.exec_()

    ############################

    # import os
    # import sys
    # import ctypes
    # import platform
    #
    # os.environ['QT_PLUGIN_PATH'] = r'E:\mambaforge\envs\pyside6\Library\lib\qt6\plugins'
    #
    # from PySide6 import QtCore
    # from PySide6.QtWidgets import QApplication, QStyleFactory
    # from fmpy.gui.MainWindow import MainWindow
    #
    # if os.name == 'nt' and int(platform.release()) >= 8:
    #     ctypes.windll.shcore.SetProcessDpiAwareness(True)
    #
    # QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    #
    # app = QApplication(sys.argv)
    #
    # print(QStyleFactory.keys())
    #
    # app.setStyle(QStyleFactory.create('WindowsVista'))
    # # app.setStyle(QStyleFactory.create('Fusion'))
    #
    # window = MainWindow()
    # window.show()
    #
    # for i, v in enumerate(sys.argv[1:]):
    #     if i > 0:
    #         window = MainWindow()
    #         window.show()
    #     window.load(v)
    #
    # sys.exit(app.exec_())
