from distutils.core import setup

setup(name = "FMPy",
      version = "0.0.5",
      description = "Simulate Functional Mockup Units (FMUs) in Python",
      author = "Torsten Sommer",
      author_email = "torsten.sommer@3ds.com",
      url = "https://github.com/CATIA-Systems/FMPy",
      license = "Standard 3-clause BSD",
      packages = ['fmpy', 'fmpy.examples'],
      package_data = {'fmpy': ['schema/fmi1/*.xsd', 'schema/fmi2/*.xsd']}
)
