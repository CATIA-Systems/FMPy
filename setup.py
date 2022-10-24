import os
from setuptools import setup

# compile Qt UI and resources
try:
    from fmpy.gui import compile_resources
    compile_resources()
except Exception as e:
    print("Failed to compile Qt UI and resources. {e}")

# generate Modelica examples
try:
    from fmpy.modelica import generate_examples
    generate_examples()
except Exception as e:
    print("Failed to generate Modelica examples. {e}")

long_description = """
FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0 for Co-Simulation and Model Exchange
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
    'fmpy.modelica',
    'fmpy.ssp',
    'fmpy.sundials',
    'fmpy.webapp'
]


def modelica_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


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
        'fmucontainer/templates/FMI2.xml',
        'modelica/FMI/package.order',
        'modelica/FMI/*.mo',
        'modelica/FMI/package.order',
        'modelica/FMI/Examples/*.mo',
        'modelica/FMI/Examples/package.order',
        'modelica/FMI/Examples/FMI2/package.mo',
        'modelica/FMI/Examples/FMI2/package.order',
        'modelica/FMI/Examples/FMI2/CoSimulation/*.mo',
        'modelica/FMI/Examples/FMI2/CoSimulation/package.order',
        'modelica/FMI/Examples/FMI2/ModelExchange/*.mo',
        'modelica/FMI/Examples/FMI2/ModelExchange/package.order',
        'modelica/FMI/Examples/FMI3/package.mo',
        'modelica/FMI/Examples/FMI3/package.order',
        'modelica/FMI/Examples/FMI3/CoSimulation/*.mo',
        'modelica/FMI/Examples/FMI3/CoSimulation/package.order',
        'modelica/FMI/Examples/FMI3/ModelExchange/*.mo',
        'modelica/FMI/Examples/FMI3/ModelExchange/package.order',
        'modelica/FMI/FMI2/package.mo',
        'modelica/FMI/FMI2/package.order',
        'modelica/FMI/FMI2/Functions/*.mo',
        'modelica/FMI/FMI2/Functions/package.order',
        'modelica/FMI/FMI2/Interfaces/*.mo',
        'modelica/FMI/FMI2/Interfaces/package.order',
        'modelica/FMI/FMI3/package.mo',
        'modelica/FMI/FMI3/package.order',
        'modelica/FMI/FMI3/Functions/*.mo',
        'modelica/FMI/FMI3/Functions/package.order',
        'modelica/FMI/FMI3/Interfaces/*.mo',
        'modelica/FMI/FMI3/Interfaces/package.order',
        'modelica/FMI/FMI3/Types/*.mo',
        'modelica/FMI/FMI3/Types/package.order',
        'modelica/FMI/Resources/FMUs/*/binaries/darwin64/*.dylib',
        'modelica/FMI/Resources/FMUs/*/binaries/linux64/*.so',
        'modelica/FMI/Resources/FMUs/*/binaries/win64/*.dll',
        'modelica/FMI/Resources/FMUs/*/binaries/x86_64-darwin/*.dylib',
        'modelica/FMI/Resources/FMUs/*/binaries/x86_64-linux/*.so',
        'modelica/FMI/Resources/FMUs/*/binaries/x86_64-windows/*.dll',
        'modelica/FMI/Resources/FMUs/*/documentation/index.html',
        'modelica/FMI/Resources/FMUs/*/documentation/LICENSE.txt',
        'modelica/FMI/Resources/FMUs/*/documentation/*.csv',
        'modelica/FMI/Resources/FMUs/*/documentation/*.svg',
        'modelica/FMI/Resources/FMUs/*/sources/buildDescription.xml',
        'modelica/FMI/Resources/FMUs/*/sources/*.c',
        'modelica/FMI/Resources/FMUs/*/sources/*.h',
        'modelica/FMI/Resources/FMUs/*/modelDescription.xml',
        'modelica/FMI/Resources/Include/ModelicaUtilityFunctions.c',
        'modelica/FMI/Resources/Include/ModelicaUtilityFunctions.h',
        'modelica/FMI/Resources/FMI_bare.png',
        'modelica/FMI/Resources/Library/darwin64/ModelicaFMI.dylib',
        'modelica/FMI/Resources/Library/linux64/ModelicaFMI.so',
        'modelica/FMI/Resources/Library/win32/ModelicaFMI.dll',
        'modelica/FMI/Resources/Library/win64/ModelicaFMI.dll',
        'modelica/templates/FMI2_CS.mo',
        'modelica/templates/FMI2_ME.mo',
        'modelica/templates/FMI3_CS.mo',
        'modelica/templates/FMI3_ME.mo',
        'modelica/templates/FMU.mo',
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
    'pywin32;platform_system=="Windows"',
    'pytz'
]

extras_require = {
    'examples': ['dask[bag]', 'requests'],
    'plot': ['matplotlib', 'scipy'],
    'gui': ['PyQt5', 'pyqtgraph'],
    'notebook': ['notebook', 'plotly'],
    'webapp': ['dash-bootstrap-components>=1.0.0']
}

extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(name='FMPy',
      version='0.3.12',
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
