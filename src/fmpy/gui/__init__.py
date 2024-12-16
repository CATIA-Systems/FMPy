""" This package contains the graphical user interface based on PySide6 """


def compile_resources():
    """ Compile the .ui and .qrc files if they are available and newer than the compiled .py files """

    import os
    from pathlib import Path
    from subprocess import check_call
    from os.path import getmtime
    import PySide6

    
    pyside_dir = Path(PySide6.__file__).parent

    if os.name == 'posix':
        pyside_dir = pyside_dir / 'Qt' / 'libexec'

    gui_dir = Path(__file__).parent
    forms_dir = gui_dir / 'forms'
    generated_dir = gui_dir / 'generated'

    # compile the forms
    if forms_dir.is_dir():

        for file in os.listdir(forms_dir):

            if not file.endswith('.ui'):
                continue

            form = os.path.basename(file)
            form, _ = os.path.splitext(form)

            ui_file = forms_dir / f'{form}.ui'
            py_file = generated_dir / f'{form}.py'

            if os.path.isfile(ui_file):
                if not py_file.is_file() or getmtime(ui_file) > os.path.getmtime(py_file):
                    print(f"UIC'ing {ui_file}")
                    uic = pyside_dir / 'uic'
                    check_call([uic, ui_file, '-o', py_file, '-g', 'python', '--from-imports'])

    icons_qrc = gui_dir / 'icons' / 'icons.qrc'
    icons_rc_py = generated_dir / 'icons_rc.py'

    # compile the resources
    if icons_qrc.is_file():
        if not icons_rc_py.is_file() or getmtime(icons_qrc) > getmtime(icons_rc_py):
            print(f"RCC'ing {icons_qrc}")
            rcc = pyside_dir / 'rcc'
            check_call([rcc, icons_qrc, '-o', icons_rc_py, '-g', 'python'])
