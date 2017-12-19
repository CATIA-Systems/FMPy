from setuptools import setup


setup(name="FMPy",
      version="0.1.1",
      description="Simulate Functional Mock-up Units (FMUs) in Python",
      long_description="""
FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0
- supports Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- can validate FMUs
- provides fixed and variable-step solvers
- is pure Python (with ctypes)
""",
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 3-clause BSD",
      packages=['fmpy',
                'fmpy.cross_check',
                'fmpy.examples',
                'fmpy.ssp',
                'fmpy.ssp.examples',
                'fmpy.sundials'],
      package_data={'fmpy':     ['schema/fmi1/*.xsd',
                                 'schema/fmi2/*.xsd',
                                 'sundials/darwin64/*.dylib',
                                 'sundials/linux64/*.so',
                                 'sundials/win32/*.dll',
                                 'sundials/win64/*.dll'],
                    'fmpy.ssp': ['schema/*.xsd']},
      install_requires=['dask[bag]',
                        'lxml',
                        'matplotlib',
                        'numpy',
                        'pathlib',
                        'requests',
                        'pypiwin32;platform_system=="Windows"'],
      entry_points={'console_scripts': ['fmpy=fmpy.command_line:main']})
