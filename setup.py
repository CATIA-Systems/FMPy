from setuptools import setup


def readme():
    """ Get the content of README.rst without the CI badges """
    with open('README.rst') as f:
        lines = f.readlines()
        while not lines[0].startswith('FMPy'):
            lines = lines[1:]
        return ''.join(lines)


setup(name="FMPy",
      version="0.0.9",
      description="Simulate Functional Mockup Units (FMUs) in Python",
      long_description=readme(),
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 3-clause BSD",
      packages=['fmpy',
                'fmpy.cross_check',
                'fmpy.examples',
                'fmpy.ssp',
                'fmpy.sundials'],
      package_data={'fmpy':     ['schema/fmi1/*.xsd',
                                 'schema/fmi2/*.xsd',
                                 'sundials/darwin64/*.dylib',
                                 'sundials/linux64/*.so',
                                 'sundials/win32/*.dll',
                                 'sundials/win64/*.dll'],
                    'fmpy.ssp': ['schema/*.xsd']})
