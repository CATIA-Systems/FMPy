from setuptools import setup

# compile Qt UI and resources
try:
    from fmpy.gui import compile_resources
    compile_resources()
except Exception as e:
    print("Failed to compile Qt UI and resources. %s" % e)

long_description = """
FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0 for Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- has a graphical user interface
- compiles C code FMUs and generates CMake projects for debugging 
"""

packages = ['fmpy',
            'fmpy.cross_check',
            'fmpy.cswrapper',
            'fmpy.examples',
            'fmpy.fmucontainer',
            'fmpy.logging',
            'fmpy.gui',
            'fmpy.gui.generated',
            'fmpy.ssp',
            'fmpy.sundials',
            'fmpy.webapp']

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
        'fmucontainer/sources/FMUContainer.c',
        'fmucontainer/sources/mpack.c',
        'fmucontainer/sources/mpack.h',
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
    'lark-parser',
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
      version='0.3.4',
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
