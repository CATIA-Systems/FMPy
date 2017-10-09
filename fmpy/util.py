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
    if np.any(np.diff(time) < 0):
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
    """ Validate a signal y(t) against a reference signal y_ref(t_ref)

        t       time of the signal
        y       values of the signal
        t_ref   time of the reference signal
        y_ref   values of the reference signal

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

    return t_band, y_min, y_max, i_out


def validate_result(result, reference):

    t_ref = reference[reference.dtype.names[0]]
    t_res = result[result.dtype.names[0]]

    rel_out = 0

    for name in result.dtype.names[1:]:

        if name not in reference.dtype.names:
            continue

        y_ref = reference[name]
        y_res = result[name]
        _, _, _, outliers = validate_signal(t=t_res, y=y_res, t_ref=t_ref, y_ref=y_ref)
        rel_out = np.max([np.sum(outliers) / float(len(outliers)), rel_out])

    return rel_out


def plot_result(result, reference=None, filename=None, window_title=None):
    """ Plot a collection of time series.

    Arguments:
        :param result:       structured NumPy Array that contains the time series to plot where 'time' is the independent variable
        :param reference:    optional reference signals with the same structure as `result`
        :param filename:     when provided the plot is saved as `filename` instead of showing the figure
        :param window_title: the title for the figure window
    """

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

    # plat at most 20 signals
    names = result.dtype.names[1:20]

    if len(names) > 0:

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

            ax.plot(time, y, color='b', linewidth=0.9, label='result', zorder=101)

            if len(name) < 18:
                ax.set_ylabel(name)
            else:
                # shorten long variable names
                ax.set_ylabel('...' + name[-15:])

            # align the y-labels
            ax.get_yaxis().set_label_coords(-0.07, 0.5)

            ax.margins(x=0, y=0.05)

        # set the window title
        if window_title is not None:
            fig.canvas.set_window_title(window_title)

        # update layout when plot is resized
        def onresize(event):
            plt.tight_layout()

        fig.canvas.mpl_connect('resize_event', onresize)

        fig.set_size_inches(w=8, h=1.5*len(names), forward=True)
        plt.tight_layout()

        if filename is None:
            plt.show()
        else:
            dir, _ = os.path.split(filename)
            if not os.path.isdir(dir):
                os.makedirs(dir)
            fig.savefig(filename=filename)
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

