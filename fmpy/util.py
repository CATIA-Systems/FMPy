import os
import numpy as np


class ValidationError(Exception):

    pass


def read_csv(filename, variable_names=[], validate=True, structured=False):
    """ Read a CSV file that conforms to the FMI cross-check rules

    Parameters:
        filename         name of the CSV file to read
        variable_names   list of variables to read (default: read all)
        structured       convert structured names to arrays

    Returns:
        traj             the trajectories read from the CSV file
    """

    # pass an empty string as deletechars to preserve special characters
    traj = np.genfromtxt(filename, delimiter=',', names=True, deletechars='')

    if structured:
        arrays = {}

        cols = []
        traj_ = []

        for name, type_ in traj.dtype.descr:
            if name.endswith(']'):
                i = name.rfind('[')
                basename = name[:i]
                if basename not in arrays:
                    arrays[basename] = []
                arrays[basename].append((int(name[i + 1:-1]) - 1, traj[name]))
            else:
                cols.append((name, type_))
                traj_.append(traj[name].tolist())

        for name, value in arrays.items():
            subs, arrs = zip(*value)
            cols.append((name, '<f8', (max(subs) + 1,)))
            traj_.append(list(zip(*arrs)))

        traj = np.array(list(zip(*traj_)), dtype=np.dtype(cols))

    if not validate:
        return traj

    # get the time
    time = traj[traj.dtype.names[0]]

    # check if the time is monotonically increasing
    if traj.size > 1 and np.any(np.diff(time) < 0):
        raise ValidationError("Values in first column (time) are not monotonically increasing")

    # get the trajectory names (without the time)
    traj_names = traj.dtype.names[1:]

    # check if the variable names match the trajectory names
    for variable_name in variable_names:
        if variable_name not in traj_names:
            raise ValidationError("Trajectory of '" + variable_name + "' is missing")

    return traj


def write_csv(filename, result, columns=None):
    """ Save a simulation result as a CSV file

    Parameters:
        filename   name of the CSV file to write
        result     structured NumPy array that holds the result
        columns    list of column names to save (None: save all)
    """

    if columns is not None:
        result = result[['time'] + columns]

    # serialize multi-dimensional signals
    cols = []
    data = []

    for name in result.dtype.names:
        dtype = result.dtype[name]
        if len(dtype.shape) > 0:
            subtype = dtype.subdtype[0].type
            y = result[name]
            for i in np.ndindex(dtype.shape):
                # convert index to 1-based subscripts
                subs = ','.join(map(lambda sub: str(sub + 1), i))
                cols.append(('%s[%s]' % (name, subs), subtype))
                sl = [slice(0, None)] + [slice(s, s + 1) for s in i]
                data.append(y[sl].flatten())
        else:
            cols.append((name, dtype.type))
            data.append(result[name])

    result = np.array(list(zip(*data)), dtype=np.dtype(cols))

    header = ','.join(map(lambda s: '"' + s + '"', result.dtype.names))
    np.savetxt(filename, result, delimiter=',', header=header, comments='', fmt='%g')


def read_ref_opt_file(filename):

    opts = {}

    with open(filename, 'r') as f:
        for line in f:
            segments = line.split(',')
            if len(segments) == 2:
                opts[segments[0]] = float(segments[1])

    # check for required elements
    for element in ['StepSize', 'StartTime', 'StopTime', 'RelTol']:
        if not element in opts:
            raise Exception("Missing element '%s'" % element)

    start_time = opts['StartTime']
    stop_time = opts['StopTime']
    step_size = opts['StepSize']

    if start_time >= stop_time:
        raise Exception("StartTime must be < StopTime")

    if step_size < 0 or step_size > (stop_time - start_time):
        raise Exception("StepSize must be >= 0 and <= (StopTime - StartTime)")

    return opts


def validate_signal(t, y, t_ref, y_ref, num=1000, dx=20, dy=0.1):
    """ Validate a signal y(t) against a reference signal y_ref(t_ref) by creating a band
    around y_ref and finding the values in y outside the band

    Parameters:

        t       time of the signal
        y       values of the signal
        t_ref   time of the reference signal
        y_ref   values of the reference signal
        num     number of samples for the band
        dx      horizontal width of the band in samples
        dy      vertical distance of the band to y_ref

    Returns:

        t_band  time values of the band
        y_min   lower limit of the band
        y_max   upper limit of the band
        i_out   indices of the values in y outside the band
    """

    from scipy.ndimage.filters import maximum_filter1d, minimum_filter1d
    from scipy.interpolate import interp1d

    # re-sample the reference signal into a uniform grid
    t_band = np.linspace(start=t_ref[0], stop=t_ref[-1], num=num)

    # make t_ref strictly monotonic by adding epsilon to duplicate sample times
    for i in range(1, len(t_ref)):
        while t_ref[i - 1] >= t_ref[i]:
            t_ref[i] = t_ref[i] + 1e-13

    interp_method = 'linear' if y.dtype == np.float64 else 'zero'
    y_band = interp1d(x=t_ref, y=y_ref, kind=interp_method)(t_band)

    y_band_min = np.min(y_band)
    y_band_max = np.max(y_band)

    # calculate the width of the band
    if y_band_min == y_band_max:
        w = 0.5 if y_band_min == 0 else np.abs(y_band_min) * dy
    else:
        w = (y_band_max - y_band_min) * dy

    # calculate the lower and upper limits
    y_min = minimum_filter1d(input=y_band, size=dx) - w
    y_max = maximum_filter1d(input=y_band, size=dx) + w

    # find outliers
    y_min_i = np.interp(x=t, xp=t_band, fp=y_min)
    y_max_i = np.interp(x=t, xp=t_band, fp=y_max)
    i_out = np.logical_or(y < y_min_i, y > y_max_i)

    # do not count outliers outside the t_ref
    i_out = np.logical_and(i_out, t > t_band[0])
    i_out = np.logical_and(i_out, t < t_band[-1])

    return t_band, y_min, y_max, i_out


def validate_fmu(filename):
    """ Validate an FMU

    Returns:
        a list of the problems found
    """

    from . import read_model_description

    try:
        read_model_description(filename, validate=True, validate_variable_names=True, validate_model_structure=True)
    except Exception as e:
        return [str(e)]

    return []


def validate_result(result, reference, stop_time=None):
    """ Validate a simulation result against a reference result

    Parameters:
        result      structured NumPy array where the first column is the time
        reference   same as result

    Returns:
        rel_out     the largest relative deviation of all signals
    """

    t_ref = reference[reference.dtype.names[0]]
    t_res = result[result.dtype.names[0]]

    # at least two samples are required
    if result.size < 2:
        return 1

    # check if stop time has been reached
    if stop_time is not None and t_res[-1] < stop_time:
        return 1

    rel_out = 0

    # find the signal with the most outliers
    for name in result.dtype.names[1:]:

        if name not in reference.dtype.names:
            continue

        y_ref = reference[name]
        y_res = result[name]
        _, _, _, outliers = validate_signal(t=t_res, y=y_res, t_ref=t_ref, y_ref=y_ref)
        rel_out = np.max([np.sum(outliers) / float(len(outliers)), rel_out])

    return rel_out


def plot_result(result, reference=None, names=None, filename=None, window_title=None, events=False):
    """ Plot a collection of time series.

    Parameters:
        result:       structured NumPy Array that contains the time series to plot where 'time' is the independent variable
        reference:    optional reference signals with the same structure as `result`
        names:        variables to plot
        filename:     when provided the plot is saved as `filename` instead of showing the figure
        window_title: title for the figure window
        events:       draw vertical lines at events
    """

    import matplotlib.pylab as pylab
    import matplotlib.pyplot as plt
    import matplotlib.transforms as mtransforms
    from matplotlib.ticker import MaxNLocator
    from collections.abc import Iterable

    params = {
        'legend.fontsize': 8,
        'axes.labelsize': 8,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'axes.linewidth': 0.5,
    }

    pylab.rcParams.update(params)

    time = result['time']

    if names is None:
        # plot at most 20 signals
        names = result.dtype.names[1:20]

    if len(names) > 0:

        # indent label 0.015 inch / character
        label_x = -0.015 * np.max(list(map(len, names)) + [8])

        fig, axes = plt.subplots(len(names), sharex=True)

        fig.set_facecolor('white')

        if not isinstance(axes, Iterable):
            axes = [axes]

        if events:
            t_event = time[np.argwhere(np.diff(time) == 0)]

        for ax, name in zip(axes, names):

            y = result[name]

            ax.grid(b=True, which='both', color='0.8', linestyle='-', zorder=0)

            ax.tick_params(direction='in')

            if events:
                for t in t_event:
                    ax.axvline(x=t, color='y', linewidth=1)

            if reference is not None and name in reference.dtype.names:
                t_ref = reference[reference.dtype.names[0]]
                y_ref = reference[name]

                t_band, y_min, y_max, i_out = validate_signal(t=time, y=y, t_ref=t_ref, y_ref=y_ref)

                ax.fill_between(t_band, y_min, y_max, facecolor=(0, 0.5, 0), alpha=0.1)
                ax.plot(t_band, y_min, color=(0, 0.5, 0), linewidth=1, label='lower bound', zorder=101, alpha=0.5)
                ax.plot(t_band, y_max, color=(0, 0.5, 0), linewidth=1, label='upper bound', zorder=101, alpha=0.5)

                # mark the outliers
                # use the data coordinates for the x-axis and the axes coordinates for the y-axis
                trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)
                ax.fill_between(time, 0, 1, where=i_out, facecolor='red', alpha=0.5, transform=trans)

            if y.dtype == np.float64:
                # find left indices of discontinuities
                i_disc = np.flatnonzero(np.diff(time) == 0)
                i_disc = np.append(i_disc + 1, len(time))
                i0 = 0
                for i1 in i_disc:
                    ax.plot(time[i0:i1], y[i0:i1], color='b', linewidth=0.9, label='result', zorder=101)
                    i0 = i1
            else:
                ax.hlines(y[:-1], time[:-1], time[1:], colors='b', linewidth=1, label='result', zorder=101)
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))

            if y.dtype == bool:
                # use fixed range and labels and fill area
                ax.set_ylim(-0.25, 1.25)
                ax.yaxis.set_ticks([0, 1])
                ax.yaxis.set_ticklabels(['false', 'true'])
                if y.ndim == 1:
                    ax.fill_between(time, y, 0, step='post', facecolor='b', alpha=0.1)
            else:
                ax.margins(x=0, y=0.05)

            if time.size < 200:
                ax.scatter(time, y, color='b', s=5, zorder=101)

            ax.set_ylabel(name, horizontalalignment='left', rotation=0)

            # align the y-labels
            ax.get_yaxis().set_label_coords(label_x, 0.5)

        # set the window title
        if window_title is not None:
            fig.canvas.set_window_title(window_title)

        def onresize(event):
            fig = plt.gcf()

            w = fig.get_figwidth()

            # tight_layout() crashes on very small figures
            if w < 3:
                return

            x = label_x * (8.0 / w)

            # update label coordinates
            for ax in fig.get_axes():
                ax.get_yaxis().set_label_coords(x, 0.5)

            # update layout
            plt.tight_layout()

        # update layout when the plot is re-sized
        fig.canvas.mpl_connect('resize_event', onresize)

        fig.set_size_inches(w=8, h=1.5 * len(names), forward=True)

        plt.tight_layout()

        if filename is None:
            plt.show()
        else:
            dir, _ = os.path.split(filename)
            if not os.path.isdir(dir):
                os.makedirs(dir)
            fig.savefig(filename)
            plt.close(fig)


def fmu_path_info(path):
    """ Extract information from the FMU's file path """
    
    head = path
    values = []

    while True:
        head, tail = os.path.split(head)

        if not tail:
            break

        values.append(tail)

        if tail == 'FMI_1.0' or tail == 'FMI_2.0':
            break

    keys = ['model_name', 'tool_version', 'tool_name', 'platform', 'fmi_type', 'fmi_version']

    return dict(zip(keys, values))


def sha256_checksum(filename):
    """ Create a SHA256 checksum form a file """

    import hashlib

    sha256 = hashlib.sha256()

    with open(filename, 'rb') as f:
        for block in iter(lambda: f.read(65536), b''):
            sha256.update(block)

    return sha256.hexdigest()


def download_file(url, checksum=None):
    """ Download a file to the current directory """

    filename = os.path.basename(url)

    if checksum is not None and os.path.isfile(filename):
        hash = sha256_checksum(filename)
        if hash.startswith(checksum.lower()):
            return  # file already exists

    import requests

    print('Downloading ' + url)

    status_code = -1

    # try to download the file three times
    try:
        for _ in range(3):
            if status_code != 200:
                response = requests.get(url)
                status_code = response.status_code
    except:
        pass  # ignore

    if status_code != 200:
        raise Exception("Failed to download %s (status code: %d)" % (url, status_code))

    # write the file
    with open(filename, 'wb') as f:
        f.write(response.content)

    if checksum is not None:
        hash = sha256_checksum(filename)
        if not hash.startswith(checksum):
            raise Exception("%s has the wrong SHA256 checksum. Expected %s but was %s." % (filename, checksum, hash))


def download_test_file(fmi_version, fmi_type, tool_name, tool_version, model_name, filename):
    """ Download a file from the Test FMUs repository to the current directory """

    from . import platform

    # for backwards compatibility
    if fmi_type == 'ModelExchange':
        fmi_type = 'me'
    elif fmi_type == 'CoSimulation':
        fmi_type = 'cs'

    # build the URL
    url = 'https://github.com/modelica/fmi-cross-check/raw/master/fmus'
    url = '/'.join([url, fmi_version, fmi_type, platform, tool_name, tool_version, model_name, filename])

    download_file(url)


def fmu_info(filename, causalities=['input', 'output']):
    """ Dump the info for an FMU """

    from .model_description import read_model_description
    from . import supported_platforms

    md = read_model_description(filename, validate=False)
    platforms = supported_platforms(filename)

    fmi_types = []
    if md.modelExchange is not None:
        fmi_types.append('Model Exchange')
    if md.coSimulation is not None:
        fmi_types.append('Co-Simulation')

    l = []

    l.append("")
    l.append("Model Info")
    l.append("")
    l.append("  FMI Version       %s" % md.fmiVersion)
    l.append("  FMI Type          %s" % ', '.join(fmi_types))
    l.append("  Model Name        %s" % md.modelName)
    l.append("  Description       %s" % md.description)
    l.append("  Platforms         %s" % ', '.join(platforms))
    l.append("  Continuous States %s" % md.numberOfContinuousStates)
    l.append("  Event Indicators  %s" % md.numberOfEventIndicators)
    l.append("  Variables         %s" % len(md.modelVariables))
    l.append("  Generation Tool   %s" % md.generationTool)
    l.append("  Generation Date   %s" % md.generationDateAndTime)

    if md.defaultExperiment:

        ex = md.defaultExperiment

        l.append("")
        l.append('Default Experiment')
        l.append("")
        if ex.startTime:
            l.append("  Start Time        %g" % ex.startTime)
        if ex.stopTime:
            l.append("  Stop Time         %g" % ex.stopTime)
        if ex.tolerance:
            l.append("  Tolerance         %g" % ex.tolerance)
        if ex.stepSize:
            l.append("  Step Size         %g" % ex.stepSize)

    inputs = []
    outputs = []

    for v in md.modelVariables:
        if v.causality == 'input':
            inputs.append(v.name)
        if v.causality == 'output':
            outputs.append(v.name)

    l.append("")
    l.append("Variables (%s)" % ', '.join(causalities))
    l.append("")
    l.append('Name                Causality              Start Value  Unit     Description')
    for v in md.modelVariables:
        if v.causality not in causalities:
            continue

        start = str(v.start) if v.start is not None else ''

        unit = v.declaredType.unit if v.declaredType else v.unit

        args = ['' if s is None else str(s) for s in [v.name, v.causality, start, unit, v.description]]

        l.append('{:19} {:10} {:>23}  {:8} {}'.format(*args))

    return '\n'.join(l)


def visual_studio_installation_path():
    """ Get the VisualStudio 2017 installation path """

    try:
        from subprocess import Popen, PIPE
        import os
        vswhere = '"' + os.environ['ProgramFiles(x86)'] + r'\Microsoft Visual Studio\Installer\vswhere.exe"'
        command = vswhere +  ' -latest -products * -requires Microsoft.Component.MSBuild -property installationPath'
        proc = Popen(command, stdout=PIPE)
        output, _ = proc.communicate()
        return output.decode('utf-8').strip()
    except Exception as e:
        pass  # do noting

    return None


def visual_c_versions():
    """ Detect installed Visual C compilers

    Returns: a sorted list of detected Visual C versions e.g. [90, 120, 140]
    """

    versions = []

    # up to Visual Studio 2015
    for key in os.environ.keys():
        if key.upper().startswith('VS') and key.upper().endswith('COMNTOOLS'):
            versions.append(int(key[len('VS'):-len('COMNTOOLS')]))

    # Visual Studio 2017
    installation_path = visual_studio_installation_path()

    if installation_path is not None:
        if '2017' in installation_path:
            versions.append(150)
        if '2019' in installation_path:
            versions.append(160)

    return sorted(versions)


def compile_dll(model_description, sources_dir, compiler=None):
    """ Compile the shared library

    Parameters:
        sources_dir:    directory that contains the FMU's source code
        compiler:       compiler to use (None: use Visual C on Windows, GCC otherwise)
    """

    from . import platform, sharedLibraryExtension

    if model_description.fmiVersion == '1.0':
        raise Exception("FMI 1.0 source FMUs are currently not supported")

    if compiler is None:
        if platform.startswith('win'):
            compiler = 'vc'
        else:
            compiler = 'gcc'

    include_dir = os.path.join(os.path.dirname(__file__), 'c-code')
    preprocessor_definitions = []

    source_files = []

    if len(model_description.buildConfigurations) == 0:
        raise Exception("No build configuration found.")

    build_configuration = model_description.buildConfigurations[0]

    if len(build_configuration.sourceFileSets) > 1:
        raise Exception("More than one SourceFileSet is not supported.")

    source_file_set = build_configuration.sourceFileSets[0]

    source_files += source_file_set.sourceFiles

    for definition in source_file_set.preprocessorDefinitions:
        literal = definition.name
        if definition.value is not None:
            literal += '=' + definition.value
        preprocessor_definitions.append(literal)

    if len(source_files) == 0:
        raise Exception("No source files specified in the model description.")

    target = build_configuration.modelIdentifier + sharedLibraryExtension

    print('Compiling %s...' % target)

    if compiler == 'vc':

        vc_versions = visual_c_versions()

        if len(vc_versions) == 0:
            raise Exception("No VisualStudio found")

        # use the latest version
        vc_version = vc_versions[-1]

        if vc_version < 150:
            command = r'call "%%VS%dCOMNTOOLS%%\..\..\VC\vcvarsall.bat"' % vc_version
        else:
            installation_path = visual_studio_installation_path()
            command = 'call "' + installation_path + r'\VC\Auxiliary\Build\vcvarsall.bat"'

        if platform == 'win64':
            command += ' x86_amd64'
        else:
            command += ' x86'

        command += ' && cl /LD /I. /I"%s"' % include_dir
        for definition in preprocessor_definitions:
            command += ' /D' + definition
        command += ' /Fe' + build_configuration.modelIdentifier + ' shlwapi.lib ' + ' '.join(source_files)

    elif compiler == 'gcc':

        command = ''
        if platform.startswith('win'):
            command += r'set PATH=C:\MinGW\bin;%%PATH%% && '
        command += 'gcc -c -I. -I%s' % include_dir
        if platform in ['linux32', 'linux64']:
            command += ' -fPIC'
        for definition in preprocessor_definitions:
            command += ' -D' + definition
        command += ' ' + ' '.join(source_files)
        command += ' && gcc'
        if platform != 'darwin64':
            command += ' -static-libgcc'
        command += ' -shared -o%s *.o' % target

    else:
        raise Exception("Unsupported compiler: '%s'" % compiler)

    cur_dir = os.getcwd()
    os.chdir(sources_dir)
    status = os.system(command)
    os.chdir(cur_dir)

    print(sources_dir)
    print(command)

    dll_path = os.path.join(sources_dir, target)

    if status != 0 or not os.path.isfile(dll_path):
        raise Exception('Failed to compile shared library')

    return str(dll_path)


def compile_platform_binary(filename, output_filename=None):
    """ Compile the binary of an FMU for the current platform and add it to the FMU

    Parameters:
        filename:         filename of the source code FMU
        output_filename:  filename of the FMU with the compiled binary (None: overwrite existing FMU)
    """

    from . import read_model_description, extract, platform, platform_tuple
    import zipfile
    from shutil import copyfile, rmtree

    unzipdir = extract(filename)

    model_description = read_model_description(filename)

    binary = compile_dll(model_description=model_description, sources_dir=os.path.join(unzipdir, 'sources'))

    unzipdir2 = extract(filename)

    platform_dir = os.path.join(unzipdir2, 'binaries', platform if model_description.fmiVersion in ['1.0', '2.0'] else platform_tuple)

    if not os.path.exists(platform_dir):
        os.makedirs(platform_dir)

    copyfile(src=binary, dst=os.path.join(platform_dir, os.path.basename(binary)))

    if output_filename is None:
        output_filename = filename  # overwrite the existing archive

    # create a new archive from the existing files + compiled binary
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(unzipdir2)
        for dirpath, dirnames, filenames in os.walk(unzipdir2):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_path))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_path))

    # clean up
    rmtree(unzipdir, ignore_errors=True)
    rmtree(unzipdir2, ignore_errors=True)


def add_remoting(filename):

    from . import extract, read_model_description, supported_platforms
    from shutil import copyfile, rmtree
    import zipfile
    import os

    platforms = supported_platforms(filename)

    if 'win32' not in platforms:
        raise Exception("The FMU does not support the platform \"win32\".")

    if 'win64' in platforms:
        raise Exception("The FMU already supports \"win64\".")

    model_description = read_model_description(filename)

    current_dir = os.path.dirname(__file__)
    client = os.path.join(current_dir, 'remoting', 'client.dll')
    server = os.path.join(current_dir, 'remoting', 'server.exe')
    license = os.path.join(current_dir, 'remoting', 'license.txt')

    tempdir = extract(filename)

    if model_description.coSimulation is not None:
        model_identifier = model_description.coSimulation.modelIdentifier
    else:
        model_identifier = model_description.modelExchange.modelIdentifier

    # copy the binaries & license
    os.mkdir(os.path.join(tempdir, 'binaries', 'win64'))
    copyfile(client, os.path.join(tempdir, 'binaries', 'win64', model_identifier + '.dll'))
    copyfile(server, os.path.join(tempdir, 'binaries', 'win64', 'server.exe'))
    licenses_dir = os.path.join(tempdir, 'documentation', 'licenses')
    if not os.path.isdir(licenses_dir):
        os.mkdir(licenses_dir)
    copyfile(license, os.path.join(tempdir, 'documentation', 'licenses', 'fmpy-remoting-binaries.txt'))

    # create a new archive from the existing files + remoting binaries
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(tempdir)
        for dirpath, dirnames, filenames in os.walk(tempdir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_path))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_path))

    # clean up
    rmtree(tempdir, ignore_errors=True)


def auto_interval(t):
    """ Find a nice interval that divides t into 500 - 1000 steps """

    h = 10 ** (np.round(np.log10(t)) - 3)

    n_samples = t / h

    if n_samples >= 2500:
        h *= 5
    elif n_samples >= 2000:
        h *= 4
    elif n_samples >= 1000:
        h *= 2
    elif n_samples <= 200:
        h /= 5
    elif n_samples <= 250:
        h /= 4
    elif n_samples <= 500:
        h /= 2

    return h


def change_fmu(input_file, output_file=None, start_values={}):
    """ Make changes to an FMU """

    from lxml import etree
    import zipfile
    from fmpy import extract
    from shutil import rmtree

    if output_file is None:
        output_file = input_file

    tempdir = extract(input_file)

    # read the model description
    with zipfile.ZipFile(input_file, 'r') as zf:
        xml = zf.open('modelDescription.xml')
        tree = etree.parse(xml)

    root = tree.getroot()

    # apply the start values
    for variable in root.find('ModelVariables'):
        if variable.get("name") in start_values:
            for child in variable.getchildren():
                if child.tag in ['Real', 'Integer', 'Enumeration', 'Boolean', 'String']:
                    child.set('start', start_values[variable.get("name")])

    # write the new model description
    tree.write(os.path.join(tempdir, 'modelDescription.xml'))

    # create a new archive from the modified files
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(tempdir)
        for dirpath, dirnames, filenames in os.walk(tempdir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_path))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_path))

    # clean up
    rmtree(tempdir, ignore_errors=True)


def get_start_values(filename):
    """ Get the start values of an FMU's variables

    Parameters:
        filename    the filename of the FMU

    Returns:
        a dictionary of variables_name -> start_value
    """

    from .model_description import read_model_description
    from . import extract
    from .fmi1 import FMU1Slave, FMU1Model
    from .fmi2 import FMU2Slave, FMU2Model
    from shutil import rmtree

    unzipdir = extract(filename)

    model_description = read_model_description(filename, validate=False)

    if model_description.coSimulation is not None:
        implementation = model_description.coSimulation
    else:
        implementation = model_description.modelExchange

    # instantiate and initialize the FMU
    fmu_kwargs = {
        'guid': model_description.guid,
        'modelIdentifier': implementation.modelIdentifier,
        'unzipDirectory': unzipdir,
    }

    if model_description.fmiVersion == '1.0':
        if model_description.coSimulation is not None:
            fmu = FMU1Slave(**fmu_kwargs)
        else:
            fmu = FMU1Model(**fmu_kwargs)
        fmu.instantiate()
        fmu.initialize()
    else:
        if model_description.coSimulation is not None:
            fmu = FMU2Slave(**fmu_kwargs)
        else:
            fmu = FMU2Model(**fmu_kwargs)
        fmu.instantiate()
        fmu.enterInitializationMode()
        fmu.exitInitializationMode()

    # read the start values
    start_values = {}

    for variable in model_description.modelVariables:
        try:
            vr = [variable.valueReference]

            if variable.type == 'Real':
                value = fmu.getReal(vr=vr)
                start_values[variable.name] = str(value[0])
            elif variable.type in ['Integer', 'Enumeration']:
                value = fmu.getInteger(vr=vr)
                start_values[variable.name] = str(value[0])
            elif variable.type == 'Boolean':
                value = fmu.getBoolean(vr=vr)
                start_values[variable.name] = 'true' if value[0] != 0 else 'false'
            elif variable.type == 'String':
                value = fmu.getString(vr=vr)
                start_values[variable.name] = value[0]
        except Exception as e:
            print(e)  # do nothing

    fmu.terminate()
    fmu.freeInstance()

    # clean up
    rmtree(unzipdir, ignore_errors=True)

    return start_values


def create_cmake_project(filename, project_dir):
    """ Create a CMake project from a C code FMU

    Parameters:

        filename     filename of the C code FMU
        project_dir  existing directory for the CMake project
    """

    from zipfile import ZipFile
    from fmpy import read_model_description, extract

    model_description = read_model_description(filename)

    extract(filename, unzipdir=project_dir)

    fmpy_dir = os.path.dirname(__file__)
    source_dir = os.path.join(fmpy_dir, 'c-code')

    with open(os.path.join(source_dir, 'CMakeLists.txt'), 'r') as cmake_file:
        txt = cmake_file.read()

    definitions = []

    if model_description.coSimulation is not None:
        definitions.append('CO_SIMULATION')

    if model_description.modelExchange is not None:
        definitions.append('MODEL_EXCHANGE')

    with ZipFile(filename, 'r') as archive:
        # don't add the current directory
        resources = list(filter(lambda n: not n.startswith('.'), archive.namelist()))

    # always add the binaries
    resources.append('binaries')

    # use the first source file set of the first build configuration
    build_configuration = model_description.buildConfigurations[0]
    source_file_set = build_configuration.sourceFileSets[0]

    sources = ['sources/' + file for file in source_file_set.sourceFiles]

    # substitute the variables
    txt = txt.replace('%MODEL_NAME%', model_description.modelName)
    txt = txt.replace('%MODEL_IDENTIFIER%', build_configuration.modelIdentifier)
    txt = txt.replace('%DEFINITIONS%', ' '.join(definitions))
    txt = txt.replace('%INCLUDE_DIRS%', '"' + source_dir.replace('\\', '/') + '"')
    txt = txt.replace('%SOURCES%', ' '.join(sources))
    txt = txt.replace('%RESOURCES%', '\n    '.join('"' + r + '"' for r in resources))

    with open(os.path.join(project_dir, 'CMakeLists.txt'), 'w') as outfile:
        outfile.write(txt)


def _is_string(s):
    """ Python 2 and 3 compatible type check for strings """
    
    import sys
    return isinstance(s, basestring if sys.version_info[0] == 2 else str)
