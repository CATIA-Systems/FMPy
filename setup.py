from distutils.core import setup


def readme():
    with open('README.rst') as f:
        return f.read()

setup(name="FMPy",
      version="0.0.7",
      description="Simulate Functional Mockup Units (FMUs) in Python",
      long_description=readme(),
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 3-clause BSD",
      packages=['fmpy', 'fmpy.examples'],
      package_data={'fmpy': ['schema/fmi1/*.xsd', 'schema/fmi2/*.xsd']})
