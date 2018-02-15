""" This package contains the graphical user interface based on PyQt5 """


def compile_resources():
    """ Compile the .ui and .qrc files if they are available and newer than the compiled .py files """

    import os

    p = os.path.dirname(__file__)

    for form in ['MainWindow', 'AboutDialog']:

        ui_file = os.path.join(p, 'forms', form + '.ui')
        py_file = os.path.join(p, 'generated', form + '.py')

        if os.path.isfile(ui_file):
            if not os.path.isfile(py_file) or os.path.getmtime(ui_file) > os.path.getmtime(py_file):
                print("UIC'ing %s" % ui_file)
                os.system('pyuic5 %s -o %s --import-from .' % (ui_file, py_file))

    icons_qrc = os.path.join(p, 'icons', 'icons.qrc')
    icons_rc_py = os.path.join(p, 'generated', 'icons_rc.py')

    if os.path.isfile(icons_qrc):
        if not os.path.isfile(icons_rc_py) or os.path.getmtime(icons_qrc) > os.path.getmtime(icons_rc_py):
            print("RCC'ing %s" % icons_qrc)
            os.system('pyrcc5 %s -o %s' % (icons_qrc, icons_rc_py))
