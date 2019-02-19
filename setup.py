from setuptools import setup

try:
    from fmpy.gui import compile_resources
    compile_resources()
except Exception as e:
    print("Failed to compile resources. %s" % e)


long_description = """
FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0 for Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- has a graphical user interface
- compiles C code FMUs and generates CMake projects for debugging 
"""

packages = ['fmpy', 'fmpy.cross_check', 'fmpy.examples', 'fmpy.gui', 'fmpy.gui.generated', 'fmpy.ssp',
            'fmpy.ssp.examples', 'fmpy.sundials']

package_data = {
    'fmpy': ['c-code/fmi2/*.h',
             'c-code/fmi2/*.c',
             'c-code/fmi2/CMakeLists.txt',
             'schema/fmi1/*.xsd',
             'schema/fmi2/*.xsd',
             'schema/fmi3/*.xsd',
             'sundials/darwin64/*.dylib',
             'sundials/linux64/*.so',
             'sundials/win32/*.dll',
             'sundials/win64/*.dll'],
    'fmpy.gui': ['icons/app_icon.ico'],
    'fmpy.ssp': ['schema/*.xsd'],
}

install_requires = ['lxml', 'numpy', 'pathlib', 'pywin32;platform_system=="Windows"']

extras_require = {
    'examples': ['dask[bag]', 'requests'],
    'plot': ['matplotlib'],
    'gui': ['PyQt5', 'pyqtgraph']
}

extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(name='FMPy',
      version='0.2.9',
      description="Simulate Functional Mock-up Units (FMUs) in Python",
      long_description=long_description,
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 3-clause BSD",
      packages=packages,
      package_data=package_data,
      install_requires=install_requires,
      extras_require=extras_require,
      entry_points={'console_scripts': ['fmpy=fmpy.command_line:main']})
