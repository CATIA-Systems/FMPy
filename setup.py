from setuptools import setup
import os
import shutil
import distutils

# compile Qt UI and resources
try:
    from fmpy.gui import compile_resources
    compile_resources()
except Exception as e:
    print("Failed to compile Qt UI and resources. %s" % e)

# build CVode shared libraries
try:
    import tarfile
    import shutil
    from subprocess import check_call
    from fmpy import sharedLibraryExtension
    from fmpy.util import download_file, visual_c_versions

    url = 'https://computing.llnl.gov/projects/sundials/download/cvode-5.0.0.tar.gz'
    checksum = '909ae7b696ec5e10a1b13c38708adf27e9a6f9e216a64dc67924263c86add7af'

    download_file(url, checksum)

    filename = os.path.basename(url)

    print("Extracting %s" % filename)
    with tarfile.open(filename, 'r:gz') as tar:
        tar.extractall()

    print("Building CVode")
    cmake_args = [
        'cmake',
        '-B', 'cvode-5.0.0/build',
        '-D', 'EXAMPLES_ENABLE_C=OFF',
        '-D', 'BUILD_STATIC_LIBS=OFF',
        '-D', 'EXAMPLES_INSTALL=OFF',
        '-D', 'CMAKE_INSTALL_PREFIX=cvode-5.0.0/dist',
    ]

    vc_versions = visual_c_versions()

    if os.name == 'nt':

        # set a 64-bit generator
        if 160 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 16 2019', '-A', 'x64']
        elif 150 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 15 2017 Win64']
        elif 140 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 14 2015 Win64']
        elif 120 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 12 2013 Win64']
        elif 110 in vc_versions:
            cmake_args += ['-G', 'Visual Studio 11 2012 Win64']

        # link statically against the VC runtime
        cmake_args += ['-D', 'CMAKE_USER_MAKE_RULES_OVERRIDE:STRING=../OverrideMSVCFlags.cmake']

    cmake_args += ['cvode-5.0.0']

    check_call(args=cmake_args)
    check_call(args=['cmake', '--build', 'cvode-5.0.0/build', '--target', 'install', '--config', 'Release'])

    library_prefix = '' if os.name == 'nt' else 'lib'

    for shared_library in ['sundials_cvode', 'sundials_nvecserial', 'sundials_sunlinsoldense',
                           'sundials_sunmatrixdense']:
        shutil.copyfile(
            os.path.join('cvode-5.0.0', 'dist', 'lib', library_prefix + shared_library + sharedLibraryExtension),
            os.path.join('fmpy', 'sundials', shared_library + sharedLibraryExtension))
except Exception as e:
    print("Failed to compile CVode shared libraries. %s" % e)

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
    'fmpy': ['c-code/*.h',
             'c-code/CMakeLists.txt',
             'schema/fmi1/*.xsd',
             'schema/fmi2/*.xsd',
             'schema/fmi3/*.xsd',
             'sundials/sundials_*.dylib',
             'sundials/sundials_*.so',
             'sundials/sundials_*.dll'],
    'fmpy.gui': ['icons/app_icon.ico'],
    'fmpy.ssp': ['schema/*.xsd'],
}

install_requires = ['lark-parser', 'lxml', 'numpy', 'pathlib', 'pywin32;platform_system=="Windows"']

extras_require = {
    'examples': ['dask[bag]', 'requests'],
    'plot': ['matplotlib'],
    'gui': ['PyQt5', 'pyqtgraph']
}

extras_require['complete'] = sorted(set(sum(extras_require.values(), [])))

setup(name='FMPy',
      version='0.2.15',
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

# see https://www.python.org/dev/peps/pep-0425/#python-tag
platform_tag = distutils.util.get_platform().replace('-', '_').replace('.', '_')

# add the platform tag to the wheel
for dirpath, _, filenames in os.walk('dist'):
    for filename in filenames:
        if filename.endswith('-any.whl'):
            shutil.move(os.path.join(dirpath, filename),
                        os.path.join(dirpath, filename).replace('-any.whl', '-' + platform_tag + '.whl'))
