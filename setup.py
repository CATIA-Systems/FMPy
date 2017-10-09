from setuptools import setup


def readme():
    """ Get the content of README.rst without the CI badges """
    with open('README.rst') as f:
        lines = f.readlines()
        while not lines[0].startswith('FMPy'):
            lines = lines[1:]
        return ''.join(lines)

setup(name="FMPy",
      version="0.0.8",
      description="Simulate Functional Mockup Units (FMUs) in Python",
      long_description=readme(),
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 3-clause BSD",
      packages=['fmpy', 'fmpy.cross_check', 'fmpy.examples'],
      package_data={'fmpy': ['schema/fmi1/*.xsd', 'schema/fmi2/*.xsd']})
