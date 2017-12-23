""" This package contains the graphical user interface based on PyQt5 """


def compile_resources():
    """ Compile the .ui and .qrc files if they are available and newer than the compiled .py files """

    import os

    p = os.path.dirname(__file__)

    mw_ui = os.path.join(p, 'forms', 'MainWindow.ui')
    mw_py = os.path.join(p, 'generated', 'MainWindow.py')

    if os.path.isfile(mw_ui):
        if not os.path.isfile(mw_py) or os.path.getmtime(mw_ui) > os.path.getmtime(mw_py):
            print("UIC'ing %s" % mw_ui)
            os.system('pyuic5 %s -o %s --import-from .' % (mw_ui, mw_py))

    icons_qrc = os.path.join(p, 'icons', 'icons.qrc')
    icons_rc_py = os.path.join(p, 'generated', 'icons_rc.py')

    if os.path.isfile(icons_qrc):
        if not os.path.isfile(icons_rc_py) or os.path.getmtime(icons_qrc) > os.path.getmtime(icons_rc_py):
            print("RCC'ing %s" % icons_qrc)
            os.system('pyrcc5 %s -o %s' % (icons_qrc, icons_rc_py))
