""" This package contains the graphical user interface based on PyQt5 """


def compile_resources():
    """ Compile the .ui and .qrc files if they are available and newer than the compiled .py files """

    import os

    gui_dir = os.path.dirname(__file__)

    forms_dir = os.path.join(gui_dir, 'forms')
    generated_dir = os.path.join(gui_dir, 'generated')

    # compile the forms
    if os.path.isdir(forms_dir):

        for file in os.listdir(forms_dir):

            if not file.endswith('.ui'):
                continue

            form = os.path.basename(file)
            form, _ = os.path.splitext(form)

            ui_file = os.path.join(forms_dir, form + '.ui')
            py_file = os.path.join(generated_dir, form + '.py')

            if os.path.isfile(ui_file):
                if not os.path.isfile(py_file) or os.path.getmtime(ui_file) > os.path.getmtime(py_file):
                    print("UIC'ing %s" % ui_file)
                    os.system('pyuic5 %s -o %s --import-from .' % (ui_file, py_file))

    icons_qrc = os.path.join(gui_dir, 'icons', 'icons.qrc')
    icons_rc_py = os.path.join(generated_dir, 'icons_rc.py')

    # compile the resources
    if os.path.isfile(icons_qrc):
        if not os.path.isfile(icons_rc_py) or os.path.getmtime(icons_qrc) > os.path.getmtime(icons_rc_py):
            print("RCC'ing %s" % icons_qrc)
            os.system('pyrcc5 %s -o %s' % (icons_qrc, icons_rc_py))
