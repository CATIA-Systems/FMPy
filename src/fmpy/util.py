from __future__ import annotations

import shutil

from pathlib import Path

from collections.abc import Iterable

import os
from os import PathLike
from numpy.typing import NDArray
from typing import List, IO, Union

import fmpy
import numpy as np


def read_csv(filename: str | PathLike, variable_names: [str] = None) -> np.typing.NDArray:
    """ Read a CSV file that conforms to the FMI cross-check rules

    Returns:
        traj             the trajectories read from the CSV file
    """

    with open(filename, 'r') as csv:
        lines = csv.readlines()

    cols = []

    names = lines[0].rstrip().split(',')
    first = lines[1].rstrip().split(',')

    for name, literal in zip(names, first):
        n = len(literal.split(' '))
        cols.append((name.strip('"'), np.float64, (n,) if n > 1 else None))

    rows = []

    for line in lines[1:]:

        row = []

        for literal in line.rstrip().split(','):
            values = literal.split(' ')
            if len(values) > 1:
                row.append(tuple(map(float, values)))
            else:
                row.append(float(literal))
        rows.append(tuple(row))

    traj = np.array(rows, dtype=np.dtype(cols))

    if variable_names is not None:
        traj = traj[['time'] + variable_names]

    return traj


def write_csv(filename: str | PathLike, result: np.typing.NDArray, columns: [str] = None) -> None:
    """ Save a simulation result as a CSV file

    Parameters:
        filename   name of the CSV file to write
        result     structured NumPy array that holds the result
        columns    list of column names to save (None: save all)
    """

    if columns is not None:
        result = result[['time'] + columns]

    with open(filename, 'w') as csv:

        csv.write(','.join(map(lambda n: f'"{n}"', result.dtype.names)) + '\n')

        for i in range(len(result)):
            for j, name in enumerate(result.dtype.names):
                value = result[i][name]
                if isinstance(value, Iterable):
                    literal = ' '.join(map(lambda v: f'{v:.16g}', value.flatten()))
                else:
                    literal = str(value)
                if j > 0:
                    csv.write(',')
                csv.write(literal)
            csv.write('\n')


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

    from scipy.ndimage import maximum_filter1d, minimum_filter1d
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


def create_plotly_figure(result: fmpy.simulation.SimulationResult | NDArray, names: Iterable[str] | None = None, events: bool =False, time_unit: str | None = None, markers: bool = False, height: int | None = None):

    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    model_description = getattr(result, 'modelDescription', None)

    units = {}
    display_units = {}

    if model_description:

        for unit in model_description.unitDefinitions:
            if unit.displayUnits:
                display_units[unit.name] = unit.displayUnits[0]

        for v in model_description.modelVariables:
            unit = v.unit
            if unit is None and v.declaredType:
                unit = v.declaredType.unit
            units[v.name] = unit

    time = result['time']

    min_ticks = 5

    if time_unit is None:

        time_span = time[-1] - time[0]

        if time_span < min_ticks * 1e-6:
            time_unit = 'ns'
        elif time_span < min_ticks * 1e-3:
            time_unit = 'us'
        elif time_span < 1:
            time_unit = 'ms'
        elif time_span > min_ticks * 365 * 24 * 60 * 60:
            time_unit = 'years'
        elif time_span > min_ticks * 24 * 60 * 60:
            time_unit = 'days'
        elif time_span > min_ticks * 60 * 60:
            time_unit = 'h'
        elif time_span > min_ticks * 60:
            time_unit = 'min'
        else:
            time_unit = 's'

    if time_unit == 'ns':
        time *= 1e9
    elif time_unit == 'us':
        time *= 1e6
    elif time_unit == 'ms':
        time *= 1e3
    elif time_unit == 's':
        pass
    elif time_unit == 'min':
        time /= 60
    elif time_unit == 'h':
        time /= 60 * 60
    elif time_unit == 'days':
        time /= 24 * 60 * 60
    elif time_unit == 'years':
        time /= 365 * 24 * 60 * 60
    else:
        raise Exception(f'time_unit must be one of "ns", "us", "ms", "s", "min", "h", "days" or "years" but was "{time_unit}".')

    if names is None:
        # plot at most 20 signals
        names = result.dtype.names[1:20]

    trajectories = []

    for name in names:
        if not name in result.dtype.names:
            print(f"Missing variable {name}...")
            continue
        y = result[name]
        if y.ndim == 1:
            trajectories.append((name, ()))
        else:
            for index in np.ndindex(y.shape[1:]):
                trajectories.append((name, index))

    fig = make_subplots(
        rows=len(trajectories),
        cols=1,
        vertical_spacing=0.06,
        shared_xaxes=True
    )

    for i, (name, index) in enumerate(trajectories):

        y = result[name][(slice(None), *index)]

        unit = units.get(name)

        if unit in display_units:
            display_unit = display_units[unit]
            y = y * display_unit.factor + display_unit.offset
            unit = display_unit.name

        if len(index) > 0:
            name += '[' + ','.join(map(str, index)) + ']'

        args = dict(
            x=time,
            name=name,
            line=dict(color='#229AEB', width=1),
            mode='lines+markers' if markers else None,
            marker=dict(color='#229AEB', size=5)
        )

        if y.dtype in [np.float32, np.float64]:
            trace = go.Scatter(y=y, **args)
        elif y.dtype == bool:
            trace = go.Scatter(y=y.astype(int), fill='tozeroy', fillcolor='rgba(0,0,255,0.1)', line_shape='hv', **args)
            fig['layout'][f'yaxis{i + 1}'].update(tickvals=[0, 1], ticktext=['false', 'true'], range=[-0.1, 1.1], fixedrange=True)
        else:
            trace = go.Scatter(y=y, line_shape='hv', **args)

        fig.add_trace(trace, row=i + 1, col=1)

        fig['layout'][f'yaxis{i + 1}'].update(title=f"{name} [{unit}]" if unit else name)

    if events:
        for t_event in time[np.argwhere(np.diff(time) == 0).flatten()]:
            fig.add_vline(x=t_event, line={'color': '#fbe424', 'width': 1})

    if height:
        fig['layout']['height'] = height  # 160 * len(trajectories) + 30 * max(0, 5 - len(trajectories))
    else:
        fig['layout'][f'xaxis{len(trajectories)}'].update(title=f'time [{time_unit}]')

    axes_attrs = dict(showgrid=True, gridwidth=1, ticklen=0, gridcolor='LightGrey', linecolor='black', showline=True,
                      zerolinewidth=1, zerolinecolor='LightGrey')
    fig.update_xaxes(range=(time[0], time[-1]), **axes_attrs)
    fig.update_yaxes(**axes_attrs)

    fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20), plot_bgcolor='rgba(0,0,0,0)')

    return fig


def plot_result(result: fmpy.simulation.SimulationResult | NDArray,
                reference: fmpy.simulation.SimulationResult | NDArray | None = None,
                names: Iterable[str] | None = None,
                filename: str | PathLike | None = None,
                window_title=None,
                events: bool = False,
                markers: bool = False,
                height: int | None = None) -> None:
    """ Plot a collection of time series.

    Parameters:
        result:       structured NumPy Array that contains the time series to plot where 'time' is the independent variable
        reference:    optional reference signals with the same structure as `result`
        names:        variables to plot
        filename:     when provided the plot is saved as `filename` instead of showing the figure
        window_title: title for the figure window
        events:       draw vertical lines at events
        markers:      show markers
        height:       fixed height of the plot figure
    """

    figure = create_plotly_figure(result, names=names, events=events, markers=markers, height=height)

    if filename is None:
        figure.show()
    else:
        figure.write_image(filename)


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


def download_file(url: str, checksum: str = None) -> str:
    """ Download a file to the current directory

        returns the filename of the downloaded file
    """

    filename = os.path.basename(url)

    if checksum is not None and os.path.isfile(filename):
        hash = sha256_checksum(filename)
        if hash.startswith(checksum.lower()):
            return filename  # file already exists

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

    return filename


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

    return download_file(url)


def fmu_info(filename: Union[str, IO], causalities: List[str] = ['input', 'output']) -> str:
    """ Dump the info for an FMU

    Parameters:
        filename     filename of the FMU
        causalities  the causalities of the variables to include

    Returns the info as a multi line string
    """

    from .model_description import read_model_description
    from . import supported_platforms

    md = read_model_description(filename, validate=False)
    platforms = supported_platforms(filename)

    fmi_types = []
    if md.modelExchange is not None:
        fmi_types.append('Model Exchange')
    if md.coSimulation is not None:
        fmi_types.append('Co-Simulation')

    l = [f"""
Model Info

  FMI Version        {md.fmiVersion}
  FMI Type           {', '.join(fmi_types)}
  Model Name         {md.modelName}
  Description        {md.description}
  Platforms          {', '.join(platforms)}
  Continuous States  {md.numberOfContinuousStates}
  Event Indicators   {md.numberOfEventIndicators}
  Variables          {len(md.modelVariables)}
  Generation Tool    {md.generationTool}
  Generation Date    {md.generationDateAndTime}
"""]

    if md.defaultExperiment:

        ex = md.defaultExperiment

        l.append('Default Experiment')
        l.append("")
        if ex.startTime:
            l.append(f"  Start Time         {ex.startTime}")
        if ex.stopTime:
            l.append(f"  Stop Time          {ex.stopTime}")
        if ex.tolerance:
            l.append(f"  Tolerance          {ex.tolerance}")
        if ex.stepSize:
            l.append(f"  Step Size          {ex.stepSize}")

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
    l.append('  Name               Causality              Start Value  Unit     Description')
    for v in md.modelVariables:
        if v.causality not in causalities:
            continue

        name = v.name

        if len(name) > 18:
            name = '...' + name[-15:]

        start = str(v.start) if v.start is not None else ''

        unit = v.declaredType.unit if v.declaredType else v.unit
        
        args = ['' if s is None else str(s) for s in [name, v.causality, start, unit, v.description]]

        l.append('  {:18} {:10} {:>23}  {:8} {}'.format(*args))

    return '\n'.join(l)


def visual_studio_installation_paths(only_latest=False):
    """ Get the installation paths for Visual Studio 2017+ """

    paths = []

    for version in [17, 16, 15]:
        try:
            from subprocess import Popen, PIPE
            import os
            vswhere = rf'{os.environ["ProgramFiles(x86)"]}\Microsoft Visual Studio\Installer\vswhere.exe'
            command = f'"{vswhere}" -products * -version [{version},{version + 1}) -property installationPath'
            proc = Popen(command, stdout=PIPE)
            output, _ = proc.communicate()
            output = output.decode('utf-8').strip()
            if output:
                paths.append((version, output))
                if only_latest:
                    break
        except Exception as e:
            pass  # do noting

    return paths


def visual_c_versions():
    """ Detect installed Visual C compilers

    Returns: a sorted list of detected Visual C versions e.g. [90, 120, 140]
    """

    versions = set()

    # up to Visual Studio 2015
    for key in os.environ.keys():
        if key.upper().startswith('VS') and key.upper().endswith('COMNTOOLS'):
            versions.add(int(key[len('VS'):-len('COMNTOOLS')]))

    # Visual Studio from 2017
    installation_paths = visual_studio_installation_paths()

    for version, _ in installation_paths:
        versions.add(version * 10)

    return sorted(versions)


def remove_source_code(filename: str | PathLike) -> None:
    """Remove the source code from an FMU or extracted FMU"""

    from shutil import rmtree
    from lxml import etree

    filename = Path(filename)

    if filename.is_file():
        unzipdir = fmpy.extract(filename=filename)
        unzipdir = Path(unzipdir)
    else:
        unzipdir = filename

    rmtree(unzipdir / 'sources')

    model_description = fmpy.read_model_description(unzipdir)

    if model_description.fmiVersion == '2.0':
        xml = os.path.join(unzipdir, 'modelDescription.xml')
        tree = etree.parse(xml)
        for e in tree.xpath('//SourceFiles'):
            e.getparent().remove(e)
        tree.write(xml, pretty_print=True, encoding='utf-8')

    if filename.is_file():
        create_zip_archive(filename, unzipdir)
        shutil.rmtree(unzipdir)


def add_remoting(filename, host_platform, remote_platform):
    """
        win32 on win64 (SM)
        linux64 on win64 (WSL + TCP)
        win64 on linux64 (wine + TCP)
    """

    from . import extract, read_model_description, supported_platforms
    from shutil import copyfile, rmtree
    import zipfile
    from os.path import join, isdir, isfile, normpath, relpath

    platforms = supported_platforms(filename)
    current_dir = os.path.dirname(__file__)

    methods = {
        ('win64', 'win32'): 'sm',
        ('win64', 'linux64'): 'tcp',
        ('linux64', 'win64'): 'tcp'
    }

    if (host_platform, remote_platform) not in methods:
        raise Exception("Remoting is not supported for the given combination of host and remote platform.")

    if host_platform in platforms:
        raise Exception(f"The FMU already supports {host_platform}.")

    if remote_platform not in platforms:
        raise Exception(f"The FMU does not support {remote_platform}.")

    method = methods[(host_platform, remote_platform)]

    model_description = read_model_description(filename)

    license = join(current_dir, 'remoting', 'license.txt')

    if isdir(filename):
        tempdir = filename
    else:
        tempdir = extract(filename)

    if model_description.coSimulation:
        model_identifier = model_description.coSimulation.modelIdentifier
    else:
        model_identifier = model_description.modelExchange.modelIdentifier

    sl_ext = {'linux64': '.so', 'win32': '.dll', 'win64': '.dll'}
    ex_ext = {'linux64': '', 'win32': '.exe', 'win64': '.exe'}

    # copy the binaries & license
    os.makedirs(join(tempdir, 'binaries', host_platform), exist_ok=True)

    copyfile(src=join(current_dir, 'remoting', host_platform, f'client_{method}{sl_ext[host_platform]}'),
             dst=join(tempdir, 'binaries', host_platform, model_identifier + sl_ext[host_platform]))

    copyfile(src=join(current_dir, 'remoting', remote_platform, f'server_{method}{ex_ext[remote_platform]}'),
             dst=join(tempdir, 'binaries', remote_platform, f'server_{method}{ex_ext[remote_platform]}'))

    licenses_dir = join(tempdir, 'documentation', 'licenses')
    os.makedirs(licenses_dir, exist_ok=True)
    copyfile(license, join(tempdir, 'documentation', 'licenses', 'fmpy-remoting-binaries.txt'))

    if not isdir(filename):
        create_zip_archive(filename, tempdir)
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

    extract(filename, unzipdir=project_dir)

    model_description = read_model_description(project_dir)

    root = Path(__file__).parent

    with open(root / "templates" / "CMakeLists.template", 'r') as cmake_file:
        txt = cmake_file.read()

    definitions = []

    if model_description.coSimulation is not None:
        definitions.append('CO_SIMULATION')

    if model_description.modelExchange is not None:
        definitions.append('MODEL_EXCHANGE')

    definitions.append('FMI3_OVERRIDE_FUNCTION_PREFIX')

    with ZipFile(filename, 'r') as archive:
        # don't add the current directory
        resources = list(filter(lambda n: not n.startswith('.'), archive.namelist()))

    # always add the binaries
    resources.append('binaries')

    # use the first source file set of the first build configuration
    build_configuration = model_description.buildConfigurations[0]
    source_file_set = build_configuration.sourceFileSets[0]

    for definition in source_file_set.preprocessorDefinitions:
        definitions.append(f'{definition.name}={definition.value}' if definition.value else definition.name)

    sources = ['sources/' + file for file in source_file_set.sourceFiles]

    # substitute the variables
    txt = txt.replace('%FMI_VERSION%', model_description.fmiVersion[0])
    txt = txt.replace('%MODEL_NAME%', model_description.modelName)
    txt = txt.replace('%MODEL_IDENTIFIER%', build_configuration.modelIdentifier)
    txt = txt.replace('%DEFINITIONS%', ' '.join(definitions))
    txt = txt.replace('%INCLUDE_DIRS%', '"' + str((root / "c-code").absolute().as_posix()) + '"')
    txt = txt.replace('%SOURCES%', ' '.join(sources))
    txt = txt.replace('%RESOURCES%', '\n    '.join('"' + r + '"' for r in resources))

    with open(os.path.join(project_dir, 'CMakeLists.txt'), 'w') as outfile:
        outfile.write(txt)


def create_jupyter_notebook(filename, notebook_filename=None):

    import nbformat as nbf
    from fmpy import read_model_description

    if notebook_filename is None:
        notebook_filename, _ = os.path.splitext(filename)
        notebook_filename += '.ipynb'

    model_description = read_model_description(filename)

    if model_description.defaultExperiment and model_description.defaultExperiment.stopTime:
        stop_time = model_description.defaultExperiment.stopTime
    else:
        stop_time = 1

    parameters = []
    output_variables = []
    max_name = 7
    max_start = 7
    max_unit = 3
    max_output = 0

    from .simulation import _get_output_variables

    for variable in _get_output_variables(model_description):
        max_output = max(max_output, len(variable.name))
        output_variables.append((variable.name, variable.description))

    for variable in model_description.modelVariables:

        if variable.causality == 'parameter' and variable.variability in ['fixed', 'tunable']:

            name, start, unit, description = variable.name, variable.start, variable.unit, variable.description

            if description:
                description = ' '.join(description.splitlines())

            def fix(v):
                if variable.type == 'String':
                    return f"'%s'" % v.replace("'", "\\'")
                elif variable.type == 'Boolean':
                    return 'True' if v == 'true' else 'False'
                else:
                    return v

            if variable.dimensions:
                start = start.split(' ')
                start = '[' + ', '.join(map(fix, start)) + ']'
            else:
                start = fix(start)

            if unit is None and variable.declaredType is not None:
                unit = variable.declaredType.unit

            max_name = max(max_name, len(name))
            max_start = max(max_start, len(start))
            max_unit = max(max_unit, len(unit)) if unit else max_unit

            parameters.append((name, start, unit, description))

    code = "import fmpy\n"
    code += "from fmpy import *\n"
    code += "\n"
    code += "\n"
    # use relative path if possible
    if os.path.normpath(os.path.dirname(filename)) == os.path.normpath(os.path.dirname(notebook_filename)):
        code += "filename = '%s'\n" % os.path.basename(filename)
    else:
        code += "filename = r'%s'\n" % filename
    code += "\n"
    code += "start_values = {\n"
    code += "    " + "# variable".ljust(max_name + 3) + "start".rjust(max_start + 2) + "   unit".ljust(
        max_unit + 10) + "description\n"

    for name, start, unit, description in parameters:
        code += "    " + ("'" + name.replace("'", "\\'") + "':").ljust(max_name + 3) + " "
        if unit:
            code += ("(" + start).rjust(max_start + 1)
            code += (", '" + unit + "'),").ljust(max_unit + 6)
        else:
            code += start.rjust(max_start + 1) + "," + " " * (max_unit + 5)
        if description:
            code += "  # " + ' '.join(description.splitlines())
        code += "\n"

    code += "}\n"
    code += "\n"
    code += "output = [\n"
    for name, description in output_variables:
        code += "    " + ("'%s'," % name.replace("'", "\\'")).ljust(max_output + 3)
        if description:
            code += "  # " + ' '.join(description.splitlines())
        code += "\n"
    code += "]\n"
    code += "\n"
    code += "result = simulate_fmu(filename, start_values=start_values, output=output, stop_time=%s)\n" % stop_time
    code += "\n"
    code += "plot_result(result)"

    nb = nbf.v4.new_notebook()

    cells = []

    if model_description.description:
        cells.append(nbf.v4.new_markdown_cell(model_description.description))

    cells.append(nbf.v4.new_code_cell(code))

    nb['cells'] = cells

    with open(notebook_filename, 'w') as f:
        nbf.write(nb, f)


def has_wsl():
    """ Check if the Windows Subsystem for Linux (WSL) is available """

    if fmpy.system != 'windows':
        return False

    import subprocess

    try:
        subprocess.run(['wsl', '--help'])
        return True
    except:
        return False


def has_wine64():
    """ Check if the Wine 64-bit is available """

    if fmpy.system != 'linux':
        return False

    import subprocess

    try:
        subprocess.run(['wine64', '--help'])
        return True
    except:
        return False


def can_simulate(platforms, remote_platform='auto'):

    from . import platform

    if remote_platform is None:  # remoting disabled

        return platform in platforms, None

    elif remote_platform == 'auto':  # auto remoting

        if platform in platforms:
            return True, None
        elif platform == 'win64' and 'win32' in platforms:
            return True, 'win32'
        elif has_wsl() and 'linux64' in platforms:
            return True, 'linux64'
        elif has_wine64() and 'win64' in platforms:
            return True, 'win64'
        else:
            return False, None

    else:  # specific remoting

        if remote_platform == 'win32' and platform == 'win64':
            return True, remote_platform
        elif remote_platform == 'win64' and has_wine64():
            return True, remote_platform
        elif remote_platform == 'linux64' and has_wsl():
            return True, remote_platform

    return False, None


def create_zip_archive(filename: str | PathLike | IO[bytes], source_dir: str | PathLike) -> None:

    import zipfile
    import os

    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        base_path = os.path.normpath(source_dir)
        for dirpath, dirnames, filenames in os.walk(source_dir):
            for name in sorted(dirnames):
                path = os.path.normpath(os.path.join(dirpath, name))
                zf.write(path, os.path.relpath(path, base_path))
            for name in filenames:
                path = os.path.normpath(os.path.join(dirpath, name))
                if os.path.isfile(path):
                    zf.write(path, os.path.relpath(path, base_path))
