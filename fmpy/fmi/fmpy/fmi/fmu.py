
def supported_platforms(filename):
    """ Get the platforms supported by the FMU without extracting it

    Parameters:
        filename    filename of the FMU, directory with extracted FMU or file like object

    Returns:
        platforms   a list of supported platforms supported by the FMU
    """

    from .util import _is_string

    # get the files within the FMU
    if _is_string(filename) and os.path.isdir(filename):  # extracted FMU
        names = []
        for dirpath, _, filenames in os.walk(filename):
            for name in filenames:
                abspath = os.path.join(dirpath, name)
                names.append(os.path.relpath(abspath, start=filename).replace('\\', '/'))
    else:  # FMU as path or file like object
        import zipfile
        with zipfile.ZipFile(filename, 'r') as zf:
            names = zf.namelist()

    platforms = []

    # check for the C-sources
    for name in names:
        head, tail = os.path.split(name)
        if head == 'sources' and tail.endswith('.c'):
            platforms.append('c-code')
            break

    # check for *.dylib on Mac
    for name in names:
        head, tail = os.path.split(name)
        if head in {'binaries/darwin64', 'binaries/x86_64-darwin'} and tail.endswith('.dylib'):
            platforms.append('darwin64')
            break

    # check for *.so on Linux
    for bitness, architecture in [('32', 'i686'), ('64', 'x86_64')]:
        for name in names:
            head, tail = os.path.split(name)
            if head in {'binaries/linux' + bitness, 'binaries/' + architecture + '-linux'} and tail.endswith('.so'):
                platforms.append('linux' + bitness)
                break

    # check for *.dll on Windows
    for bitness, architecture in [('32', 'i686'), ('64', 'x86_64')]:
        for name in names:
            head, tail = os.path.split(name)
            if head in {'binaries/win' + bitness, 'binaries/' + architecture + '-windows'} and tail.endswith('.dll'):
                platforms.append('win' + bitness)
                break

    return platforms


def fmi_info(filename):
    """ Read the FMI version and supported FMI types from the FMU without extracting it

    Parameters:
        filename      filename of the FMU

    Returns:
        fmi_version   FMI version as a string ('1.0' or '2.0')
        fmi_types     list of supported FMI types ('CoSimulation', 'ModelExchange')
    """

    from lxml import etree
    import zipfile

    fmi_types = []

    # open the FMU
    with zipfile.ZipFile(filename, 'r') as zf:

        # read the model description
        md = zf.open('modelDescription.xml')
        tree = etree.parse(md)
        root = tree.getroot()
        fmi_version = root.get('fmiVersion')

        # get the supported FMI types
        if fmi_version == '1.0':

            if root.find('Implementation') is not None:
                fmi_types.append('CoSimulation')
            else:
                fmi_types.append('ModelExchange')

        elif fmi_version == '2.0':

            if root.find('ModelExchange') is not None:
                fmi_types.append('ModelExchange')

            if root.find('CoSimulation') is not None:
                fmi_types.append('CoSimulation')

        else:
            raise Exception("Unsupported FMI version %s" % fmi_version)

    return fmi_version, fmi_types


def extract(filename, unzipdir=None):
    """ Extract a ZIP archive to a temporary directory

    Parameters:
        filename    filename of the ZIP archive
        unzipdir    target directory (None: create temporary directory)

    Returns:
        unzipdir    path to the directory that contains the extracted files
    """

    from tempfile import mkdtemp
    import zipfile

    if unzipdir is None:
        unzipdir = mkdtemp()

    # expand the 8.3 paths on windows
    if sys.platform.startswith('win') and '~' in unzipdir:
        import win32file
        unzipdir = win32file.GetLongPathName(unzipdir)

    with zipfile.ZipFile(filename, 'r') as zf:

        # check filenames
        for name in zf.namelist():

            if '\\' in name:
                raise Exception("Illegal path %s found in %s. All slashes must be forward slashes." % (name, filename))

            if ':' in name or name.startswith('/'):
                raise Exception("Illegal path %s found in %s. The path must not contain a drive or device letter, or a leading slash." % (name, filename))

        # extract the archive
        zf.extractall(unzipdir)

    return unzipdir


def dump(filename):
    """ Print the model information and variables of an FMU

    Parameters:
        filename    filename of the FMU
    """

    from .util import fmu_info
    print(fmu_info(filename))


def instantiate_fmu(unzipdir, model_description, fmi_type=None, visible=False, debug_logging=False, logger=None, logger_proxy_add_func=None, fmi_call_logger=None, use_remoting=False):
    """
    Create an instance of fmpy.fmi1._FMU (see simulate_fmu() for documentation of the parameters).
    """

    # common constructor arguments
    fmu_args = {
        'guid': model_description.guid,
        'unzipDirectory': unzipdir,
        'instanceName': None,
        'fmiCallLogger': fmi_call_logger
    }

    if use_remoting:
        fmu_args['libraryPath'] = os.path.join(os.path.dirname(__file__), 'remoting', 'client.dll')

    if logger is None:
        logger = printLogMessage

    is_fmi1 = model_description.fmiVersion == '1.0'
    is_fmi2 = model_description.fmiVersion == '2.0'

    if is_fmi1:
        callbacks = fmi1CallbackFunctions()
        callbacks.logger         = fmi1CallbackLoggerTYPE(logger)
        callbacks.allocateMemory = fmi1CallbackAllocateMemoryTYPE(allocateMemory)
        callbacks.freeMemory     = fmi1CallbackFreeMemoryTYPE(freeMemory)
        callbacks.stepFinished   = None
    elif is_fmi2:
        callbacks = fmi2CallbackFunctions()
        callbacks.logger         = fmi2CallbackLoggerTYPE(logger)
        callbacks.allocateMemory = fmi2CallbackAllocateMemoryTYPE(allocateMemory)
        callbacks.freeMemory     = fmi2CallbackFreeMemoryTYPE(freeMemory)
    else:
        callbacks = None

    if model_description.fmiVersion in ['1.0', '2.0']:
        # add native proxy function that processes variadic arguments
        try:
            if logger_proxy_add_func:
                logger_proxy_add_func(byref(callbacks))
#            from .logging import addLoggerProxy
#            addLoggerProxy(byref(callbacks))
        except Exception as e:
            print("Failed to add logger proxy function. %s" % e)

    if fmi_type in [None, 'CoSimulation'] and model_description.coSimulation is not None:

        fmu_args['modelIdentifier'] = model_description.coSimulation.modelIdentifier

        if is_fmi1:
            fmu = FMU1Slave(**fmu_args)
            fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        elif is_fmi2:
            fmu = FMU2Slave(**fmu_args)
            fmu.instantiate(visible=visible, callbacks=callbacks, loggingOn=debug_logging)
        else:
            fmu = fmi3.FMU3Slave(**fmu_args)
            fmu.instantiate(visible=visible, loggingOn=debug_logging)

    elif fmi_type in [None, 'ModelExchange'] and model_description.modelExchange is not None:

        fmu_args['modelIdentifier'] = model_description.modelExchange.modelIdentifier

        if is_fmi1:
            fmu = FMU1Model(**fmu_args)
            fmu.instantiate(functions=callbacks, loggingOn=debug_logging)
        elif is_fmi2:
            fmu = FMU2Model(**fmu_args)
            fmu.instantiate(visible=visible, callbacks=callbacks, loggingOn=debug_logging)
        else:
            fmu = fmi3.FMU3Model(**fmu_args)
            fmu.instantiate(visible=visible, loggingOn=debug_logging)

    else:

        raise Exception('FMI type "%s" is not supported by the FMU' % fmi_type)

    return fmu
