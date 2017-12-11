import os
import numpy as np


class ValidationError(Exception):

    pass


def read_csv(filename, variable_names=[], validate=True):
    """ Read a CSV file that conforms to the FMI cross-check rules """

    # pass an empty string as deletechars to preserve special characters
    traj = np.genfromtxt(filename, delimiter=',', names=True, deletechars='')

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


def write_csv(filename, result):
    """ Save results as a CSV """
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

    # re-sample the reference signal into a uniform grid
    t_band = np.linspace(start=t_ref[0], stop=t_ref[-1], num=num)

    # sort out the duplicate samples before the interpolation
    m = np.concatenate(([True], np.diff(t_ref) > 0))

    y_band = np.interp(x=t_band, xp=t_ref[m], fp=y_ref[m])

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
    """ Validate a simulation result agains a reference result

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


def plot_result(result, reference=None, names=None, filename=None, window_title=None):
    """ Plot a collection of time series.

    Arguments:
        :param result:       structured NumPy Array that contains the time series to plot where 'time' is the independent variable
        :param reference:    optional reference signals with the same structure as `result`
        :param columns:      columns to plot
        :param filename:     when provided the plot is saved as `filename` instead of showing the figure
        :param window_title: the title for the figure window
    """

    import matplotlib
    import matplotlib.pylab as pylab
    import matplotlib.pyplot as plt
    import matplotlib.transforms as mtransforms
    from collections import Iterable

    params = {
        # 'legend.fontsize': 'medium',
        # 'figure.figsize': (10, 8),
        'legend.fontsize': 8,
        'axes.labelsize': 8,
        # 'axes.titlesize': 'medium',
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

        for ax, name in zip(axes, names):

            y = result[name]

            ax.grid(b=True, which='both', color='0.8', linestyle='-', zorder=0)

            ax.tick_params(direction='in')

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
                ax.plot(time, y, color='b', linewidth=0.9, label='result', zorder=101)
            else:
                ax.hlines(y, time[:-1], time[1:], colors='b', linewidth=1, label='result', zorder=101)
                # ax.step(time, y, where='post', color='b', linewidth=0.9, label='result', zorder=101)

            if y.dtype == bool:
                # use fixed range and labels and fill area
                ax.set_ylim(-0.25, 1.25)
                ax.yaxis.set_ticks([0, 1])
                ax.yaxis.set_ticklabels(['false', 'true'])
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
        if hash.startswith(checksum):
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
        pass

    if status_code != 200:
        raise Exception("Failed to download %s (status code: %d)" % (url, status_code))

    # write the file
    with open(filename, 'wb') as f:
        f.write(response.content)


def download_test_file(fmi_version, fmi_type, tool_name, tool_version, model_name, filename):
    """ Download a file from the Test FMUs repository to the current directory """

    from . import platform

    # build the URL
    url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_' + fmi_version
    url = '/'.join([url, fmi_type, platform, tool_name, tool_version, model_name, filename])

    download_file(url)
