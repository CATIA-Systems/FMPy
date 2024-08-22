import shutil
from pathlib import Path

from setuptools import setup

# compile Qt UI and resources
try:
    from fmpy.gui import compile_resources
    compile_resources()
except Exception as e:
    print(f"Failed to compile Qt UI and resources. {e}")

# copy the sources of the Container FMU
try:
    root = Path(__file__).parent
    for file in [
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-common.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-common.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-expect.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-expect.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-node.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-node.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-platform.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-platform.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-reader.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-reader.h',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-writer.c',
        root / 'thirdparty' / 'mpack' / 'src' / 'mpack' / 'mpack-writer.h',
        root / 'thirdparty' / 'Reference-FMUs' / 'src' / 'FMI.c',
        root / 'thirdparty' / 'Reference-FMUs' / 'include' / 'FMI.h',
        root / 'thirdparty' / 'Reference-FMUs' / 'src' / 'FMI2.c',
        root / 'thirdparty' / 'Reference-FMUs' / 'include' / 'FMI2.h',
        root / 'src' / 'fmucontainer' / 'fmi2Functions.c',
        root / 'src' / 'fmucontainer' / 'fmi3Functions.c',
        root / 'src' / 'fmucontainer' / 'FMUContainer.c',
        root / 'src' / 'fmucontainer' / 'FMUContainer.h',
    ]:
        shutil.copyfile(src=file, dst=root / 'fmpy' / 'fmucontainer' / 'sources' / file.name)
except Exception as e:
    print(f"Failed to copy sources of the Container FMU. {e}")

long_description = """
FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0, 2.0, and 3.0 for Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- has a graphical user interface
- compiles C code FMUs and generates CMake projects for debugging
"""

packages = [
    'fmpy',
    'fmpy.cross_check',
    'fmpy.cswrapper',
    'fmpy.examples',
    'fmpy.fmucontainer',
    'fmpy.gui',
    'fmpy.gui.generated',
    'fmpy.logging',
    'fmpy.ssp',
    'fmpy.sundials',
    'fmpy.webapp'
]

package_data = {
    'fmpy': [
        'c-code/*.h',
        'c-code/CMakeLists.txt',
        'cswrapper/cswrapper.dll',
        'cswrapper/cswrapper.dylib',
        'cswrapper/cswrapper.so',
        'cswrapper/license.txt',
        'logging/darwin64/logging.dylib',
        'logging/linux64/logging.so',
        'logging/win32/logging.dll',
        'logging/win64/logging.dll',
        'fmucontainer/binaries/darwin64/FMUContainer.dylib',
        'fmucontainer/binaries/linux64/FMUContainer.so',
        'fmucontainer/binaries/win32/FMUContainer.dll',
        'fmucontainer/binaries/win64/FMUContainer.dll',
        'fmucontainer/documentation/LICENSE.txt',
        'fmucontainer/sources/buildDescription.xml',
        'fmucontainer/sources/*.c',
        'fmucontainer/sources/*.h',
        'fmucontainer/templates/FMI2.xml',
        'fmucontainer/templates/FMI3.xml',
        'remoting/linux64/client_sm.so',
        'remoting/linux64/client_tcp.so',
        'remoting/linux64/server_sm',
        'remoting/linux64/server_tcp',
        'remoting/win32/client_sm.dll',
        'remoting/win32/client_tcp.dll',
        'remoting/win32/server_sm.exe',
        'remoting/win32/server_tcp.exe',
        'remoting/win64/client_sm.dll',
        'remoting/win64/client_tcp.dll',
        'remoting/win64/server_sm.exe',
        'remoting/win64/server_tcp.exe',
        'remoting/license.txt',
        'schema/fmi1/*.xsd',
        'schema/fmi2/*.xsd',
        'schema/fmi3/*.xsd',
        'sundials/x86_64-darwin/sundials_*.dylib',
        'sundials/x86_64-linux/sundials_*.so',
        'sundials/x86_64-windows/sundials_*.dll'
    ],
    'fmpy.gui': ['icons/app_icon.ico'],
    'fmpy.ssp': ['schema/*.xsd'],
    'fmpy.webapp': ['assets/*.css'],
}

install_requires = [
    'attrs',
    'Jinja2',
    'lark',
    'lxml',
    'msgpack',
    'numpy',
    'pywin32;platform_system=="Windows"'
]

extras_require = {
    'examples': ['dask[bag]', 'requests'],
    'plot': ['matplotlib', 'scipy'],
    'gui': ['PyQt5', 'pyqtgraph', 'PyQtWebEngine'],
    'notebook': ['kaleido', 'notebook', 'plotly'],
    'webapp': ['dash-bootstrap-components>=1.0.0']
}

extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(name='FMPy',
      version='0.3.21',
      description="Simulate Functional Mock-up Units (FMUs) in Python",
      long_description=long_description,
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 2-clause BSD",
      packages=packages,
      package_data=package_data,
      python_requires='>=3.5',
      install_requires=install_requires,
      extras_require=extras_require,
      entry_points={'console_scripts': ['fmpy=fmpy.command_line:main']})
