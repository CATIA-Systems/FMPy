
from setuptools import setup, find_namespace_packages

long_description = """
FMPy - FMI
==========

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`
"""

install_requires = [
    'lxml',
    'pathlib;python_version<"3.4"',
    'pywin32;platform_system=="Windows"'
]

package_data = {
    'fmpy.fmi': [
        'schema/fmi1/*.xsd',
        'schema/fmi2/*.xsd',
        'schema/fmi3/*.xsd',
    ],
}

setup(name='FMPy.fmi',
      version='0.2.23',
      description="Simulate Functional Mock-up Units (FMUs) in Python",
      long_description=long_description,
      author="Torsten Sommer",
      author_email="torsten.sommer@3ds.com",
      url="https://github.com/CATIA-Systems/FMPy",
      license="Standard 2-clause BSD",
      packages=find_namespace_packages(include=['fmpy.*']),
      package_data=package_data,
      install_requires=install_requires,
)
