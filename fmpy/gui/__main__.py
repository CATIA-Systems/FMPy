""" Entry point for the graphical user interface """

if __name__ == '__main__':

    import sys
    from PyQt5.QtWidgets import QApplication
    from fmpy.gui.MainWindow import MainWindow

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    for i, v in enumerate(sys.argv[1:]):
        if i > 0:
            window = MainWindow()
            window.show()
        window.load(v)

    sys.exit(app.exec_())
