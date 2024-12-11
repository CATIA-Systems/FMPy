
def get_vendor_ids(tools_csv):
    """ Get vendor and tool info from tools.csv

    Parameters:
        tools_csv  path to the _data/tools.csv in the fmi-standard.org repository

    Returns:
        a dictionary {vendor_id: (tool_id, tool_name)}
    """

    import csv

    vendors = {}

    with open(tools_csv, 'r') as csvfile:

        reader = csv.reader(csvfile, delimiter=',', quotechar='"')

        next(reader)  # skip the header

        for row in reader:

            tool_name, tool_id, vendor_id = row[:3]

            if vendor_id in vendors:
                vendors[vendor_id].append((tool_id, tool_name))
            else:
                vendors[vendor_id] = [(tool_id, tool_name)]

    return vendors


def validate_result(result, reference, t_start, t_stop):
    """ Validate a simulation result against a reference result

    Parameters:
        result      structured NumPy array where the first column is the time
        reference   same as result
        ...

    Returns:
        problems    a list of problems
    """

    import numpy as np

    t_ref = reference[reference.dtype.names[0]]
    t_res = result[result.dtype.names[0]]

    # at least two samples are required
    if result.size < 2:
        return 'The result must have at least two samples'

    # check if stop time has been reached
    if t_res[0] > t_start:
        return 'The result starts at %g after the start time (%g s)' % (t_res[0], t_start)

    # check if stop time has been reached
    if t_res[-1] < t_stop:
        return 'The result ends at %g s before the stop time (%g s)' % (t_res[-1], t_stop)

    # check if all reference signals are contained in the result
    for name in reference.dtype.names[1:]:
        if name not in result.dtype.names:
            return 'Variable "%s" is missing' % name

    # find the signal with the most outliers
    for name in result.dtype.names[1:]:

        if name not in reference.dtype.names:
            continue

        y_ref = reference[name]
        y_res = result[name]
        _, _, _, outliers = validate_signal(t=t_res, y=y_res, t_ref=t_ref, y_ref=y_ref, t_start=t_start, t_stop=t_stop)

        # calculate the relative number of outliers
        rel_out = np.sum(outliers) / float(len(outliers))

        if rel_out > 0.1:
            return 'More than 10%% of the samples outside epsilon band for variable "%s"' % name

    return None


def validate_signal(t, y, t_ref, y_ref, t_start, t_stop, num=1000, dx=21, dy=0.1):
    """ Validate a signal y(t) against a reference signal y_ref(t_ref) by creating a band
    around y_ref and finding the values in y outside the band

    Parameters:

        t        time of the signal
        y        values of the signal
        t_ref    time of the reference signal
        y_ref    values of the reference signal
        t_start  start time of the band
        t_stop   stop time of the band
        num      number of samples for the band
        dx       horizontal tolerance in samples
        dy       relative vertical tolerance

    Returns:

        t_band  time values of the band
        y_min   lower limit of the band
        y_max   upper limit of the band
        i_out   indices of the outliers in y
    """

    import numpy as np
    from scipy.ndimage.filters import maximum_filter1d, minimum_filter1d

    # re-sample the reference signal into a uniform grid
    t_band = np.linspace(start=t_start, stop=t_stop, num=num)

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
    i_out = np.logical_and(i_out, t >= t_start)
    i_out = np.logical_and(i_out, t <= t_stop)

    return t_band, y_min, y_max, i_out
