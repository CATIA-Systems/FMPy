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

- supports FMI 1.0 and 2.0
- supports Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- can validate FMUs
- provides fixed and variable-step solvers
- is pure Python (with ctypes)
"""

packages = ['fmpy', 'fmpy.cross_check', 'fmpy.examples', 'fmpy.gui', 'fmpy.gui.generated', 'fmpy.ssp',
            'fmpy.ssp.examples', 'fmpy.sundials']

package_data = {
    'fmpy': ['schema/fmi1/*.xsd',
             'schema/fmi2/*.xsd',
             'sundials/darwin64/*.dylib',
             'sundials/linux64/*.so',
             'sundials/win32/*.dll',
             'sundials/win64/*.dll'],
     'fmpy.ssp': ['schema/*.xsd']
}

install_requires = ['lxml', 'numpy', 'pathlib', 'pypiwin32;platform_system=="Windows"']

extras_require = {
    'examples': ['dask[bag]', 'requests'],
    'plot': ['matplotlib'],
    'gui': ['PyQt5', 'pyqtgraph']
}

extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(name='FMPy',
      version='0.1.2',
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
