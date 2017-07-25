import os
import numpy as np
import fmpy
import zipfile
from scipy.ndimage.filters import maximum_filter1d, minimum_filter1d
import matplotlib.transforms as mtransforms
import time


class ValidationError(Exception):

    pass


def read_csv(filename, variable_names=[], validate=True):

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


# noinspection PyPackageRequirements
def plot_result(result, reference=None, filename=None):

    import matplotlib.pylab as pylab
    import matplotlib.pyplot as plt
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

            ax.plot(time, y, 'b', label='result', zorder=101)

            if len(name) < 18:
                ax.set_ylabel(name)
            else:
                # shorten long variable names
                ax.set_ylabel('...' + name[-15:])

            ax.margins(x=0, y=0.05)

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


if __name__ == '__main__':
    """ Run the FMI cross-check """

    import argparse

    parser = argparse.ArgumentParser(description='run the FMI cross-check')

    parser.add_argument('--fmus_dir', default=os.getcwd(), help='the directory that contains the test FMUs')
    parser.add_argument('--report', default='report.html', help='name of the report file')
    parser.add_argument('--result_dir', help='the directory to store the results')
    parser.add_argument('--include', nargs='+', default=[], help='path segments to include')
    parser.add_argument('--exclude', nargs='+', default=[], help='path segments to exclude')
    parser.add_argument('--simulate', action='store_true', help='simulate the FMU')

    args = parser.parse_args()

    html = open(args.report, 'w')
    html.write('''<html>
    <head>
        <style>
            p, li, td, th, footer {
              font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
              font-size: 0.75em;
              line-height: 1.5em;
            }
            td.passed { background-color: #eeffee; }
            td.failed { background-color: #ffdddd; }

            td.status { text-align: center; }

            .label {
                display: inline-block;
                min-width: 35px;
                padding: .5em .6em .5em;
                font-size: 75%;
                font-weight: 700;
                line-height: 1;
                color: #fff;
                text-align: center;
                white-space: nowrap;
                vertical-align: baseline;
                border-radius: .25em;
            }

            .label-danger {
                background-color: #d9534f;
            }

            .label-warning {
                background-color: #f0ad4e;
            }

            .label-success {
                background-color: #5cb85c;
            }

            .label-default {
                background-color: #777;
            }

            .tooltip {
                position: relative;
                display: inline-block;
                border-bottom: 1px dotted black;
            }

            .tooltip .tooltiptext {
                visibility: hidden;
                width: auto;
                background-color: black;
                color: #fff;
                text-align: center;
                border-radius: 6px;
                padding: 5px;

                /* Position the tooltip */
                position: absolute;
                z-index: 1;
                right: 0;
                top: 30px;
            }

            .tooltip:hover .tooltiptext {
                visibility: visible;
            }
        </style>
    </head>
    <body>
        <table>''')
    html.write('<tr><th>Model</th><th>FMU</th><th>Opts</th><th>In</th><th>Ref</th><th>Doc</th><th>Sim</th><th>Res</th></tr>\n')

    for root, dirs, files in os.walk(args.fmus_dir):

        fmu_filename = None

        for file in files:
            if file.endswith('.fmu'):
                fmu_name, _ = os.path.splitext(file)  # FMU name without file extension
                fmu_filename = os.path.join(root, file)  # absolute path filename
                break

        if fmu_filename is None:
            continue

        def skip(include, exclude):

            for pattern in exclude:
                if pattern in fmu_filename:
                    return True

            for pattern in include:
                if pattern not in fmu_filename:
                    return True

            return False

        if skip(include=args.include, exclude=args.exclude):
            continue

        print(root)

        ##########################
        # VALIDATE FMU AND FILES #
        ##########################

        # read the model description
        try:
            model_description = fmpy.read_model_description(fmu_filename)
            xml_cell = '<td class="status"><span class="label label-success">valid</span></td>'
        except Exception as e:
            # try again without validation
            model_description = fmpy.read_model_description(fmu_filename, validate=False)
            xml_cell = '<td class="status"><span class="label label-danger" title="' + str(e) + '">invalid</span></td>'

        # check for documentation
        if model_description.fmiVersion == '1.0':
            doc_path = 'documentation/_main.html'
        else:
            doc_path = 'documentation/index.html'

        doc_cell = '<td class="status"><span class="label label-default" title="' + doc_path + " is missing" + '">n/a</span></td>'

        with zipfile.ZipFile(fmu_filename, 'r') as zf:
            if doc_path in zf.namelist():
                # TODO: validate HTML?
                doc_cell = '<td class="status"><span class="label label-success">available</span></td>'

        input_variables = []
        output_variables = []

        # collect the variable names
        for variable in model_description.modelVariables:
            if variable.causality == 'input':
                input_variables.append(variable.name)
            elif variable.causality == 'output':
                output_variables.append(variable.name)

        # check the reference options file
        try:
            ref_opts = read_ref_opt_file(os.path.join(root, fmu_name + '_ref.opt'))
            ref_opts_cell = '<td class="status"><span class="label label-success">valid</span></td>'
        except Exception as e:
            ref_opts = None
            ref_opts_cell = '<td class="status"><span class="label label-danger" title="' + str(e) + '">invalid</span></td>'

        def check_csv_file(filename, variables):
            """ Load the CSV and generate the table cell """

            try:
                # load with validation
                traj = read_csv(filename=filename, variable_names=variables)
                cell = '<td class="status"><span class="label '
                cell += 'label-warning' if traj.size > 1000 else 'label-success'
                cell += '">%d &times; %d</span></td>' % (len(traj.dtype), traj.size)
            except Exception as e1:
                try:
                    # load without validation
                    traj = read_csv(filename=filename)
                    cell = '<td class="status"><span class="label label-warning" title="' + str(e1) + '">%d &times; %d</span></td>' % (len(traj.dtype), traj.size)
                except Exception as e2:
                    traj = None
                    cell = '<td class="status"><span class="label label-danger" title="' + str(e2) + '">invalid</span></td>'

            return traj, cell


        # check the input file
        input = None

        if input_variables:
            in_path = os.path.join(root, fmu_name + '_in.csv')
            input, in_csv_cell = check_csv_file(filename=in_path, variables=input_variables)
        else:
            in_csv_cell = '<td class="status"><span class="label label-default">n/a</span></td>'

        # check the reference file
        ref_path = os.path.join(root, fmu_name + '_ref.csv')
        reference, ref_csv_cell = check_csv_file(filename=ref_path, variables=output_variables)

        supported_platforms = fmpy.supported_platforms(fmu_filename)

        # this will remove any trailing (back)slashes
        fmus_dir = os.path.normpath(args.fmus_dir)
        model_path = fmu_filename[len(fmus_dir) + 1:]
        model_path = os.path.dirname(model_path)
        fmu_simple_filename = os.path.basename(fmu_filename)
        model_name, _ = os.path.splitext(fmu_simple_filename)

        # build the filenames
        result = None

        ##############
        # SIMULATION #
        ##############

        def skip_simulation():
            """ Sort out the FMUs that crash the process """

            # fullRobot w/ ModelExchange
            if 'ModelExchange' in fmu_filename and 'fullRobot' in fmu_filename:
                return True  # cannot be solved w/ Euler

            # win64
            if r'FMI_2.0\CoSimulation\win64\FMIToolbox_MATLAB\2.1' in fmu_filename:
                return True  # instantiate() does not return in release mode

            if r'FMI_2.0\CoSimulation\win64\AMESim\15\MIS_cs' in fmu_filename:
                return True  # exitInitializationMode() does not return in release mode

            # linux64
            if 'FMI_1.0/ModelExchange/linux64/JModelica.org/1.15' in fmu_filename:
                return True  # exit code 139 (interrupted by signal 11: SIGSEGV)

            if 'FMI_1.0/ModelExchange/linux64/AMESim' in fmu_filename:
                return True  # exit code 139 (interrupted by signal 11: SIGSEGV)

            return False

        skipped = True

        if not args.simulate:
            sim_cell = '<td class="status" title="Simulation is disabled"><span class="label label-default">skipped</span></td>'
        elif ref_opts is None:
            sim_cell = '<td class="status" title="Failed to read *_ref.opt file"><span class="label label-default">skipped</span></td>'
        elif input_variables and input is None:
            sim_cell = '<td class="status" title="Input file is invalid"><span class="label label-default">skipped</span></td>'
        elif fmpy.platform not in supported_platforms:
            sim_cell = '<td class="status" title="The current platform (' + fmpy.platform + ') is not supported by the FMU (' + ', '.join(supported_platforms) + ')"><span class="label label-default">skipped</span></td>'
        elif skip_simulation():
            sim_cell = '<td class="status" title="FMU not supported (yet)"><span class="label label-warning">n/s</span></td>'
            print("Skipping simulation")
        else:
            skipped = False

            step_size = ref_opts['StepSize']

            # variable step solvers are currently not supported
            if step_size == 0:
                step_size = None

            if reference is not None:
                output_variable_names = reference.dtype.names[1:]
            else:
                output_variable_names = None

            try:
                start_time = time.time()

                # simulate the FMU
                result = fmpy.simulate_fmu(filename=fmu_filename, validate=False, step_size=step_size,
                                           stop_time=ref_opts['StopTime'], input=input, output=output_variable_names, timeout=10)

                sim_cell = '<td class="status"><span class="label label-success">%.2f s</span></td>' % (time.time() - start_time)

            except Exception as e:
                sim_cell = '<td class="status"><span class="label label-danger" title="' + str(e) + '">failed</span></td>'

        ##############
        # VALIDATION #
        ##############
        if skipped:
            res_cell = '<span class="label label-default">n/a</span>'
        else:
            try:
                rel_out = validate_result(result=result, reference=reference)
            except Exception as e:
                print(str(e))
                rel_out = 1

            res_cell = '<span class="label '

            if rel_out <= 0:
                res_cell += 'label-success'
            elif rel_out <= 0.1:
                res_cell += 'label-warning'
            else:
                res_cell += 'label-danger'

            res_cell += '">%d %%</span>' % np.floor((1.0 - rel_out) * 100)

        # this will remove any trailing (back)slashes
        fmus_dir = os.path.normpath(args.fmus_dir)

        model_path = fmu_filename[len(fmus_dir)+1:]

        model_path = os.path.dirname(model_path)

        html.write('<tr><td>' + root + '</td>')
        html.write('\n'.join([xml_cell, ref_opts_cell, in_csv_cell, ref_csv_cell, doc_cell, sim_cell]))

        if args.result_dir is not None and result is not None:

            fmu_result_dir = os.path.join(args.result_dir, model_path)

            if not os.path.exists(fmu_result_dir):
                os.makedirs(fmu_result_dir)

            result_filename = os.path.join(fmu_result_dir, 'result.csv')

            header = ','.join(map(lambda s: '"' + s + '"', result.dtype.names))
            np.savetxt(result_filename, result, delimiter=',', header=header, comments='', fmt='%g')

            reference_filename = os.path.join(fmus_dir, model_path, model_name + '_ref.csv')

            if os.path.isfile(reference_filename):
                # load the reference trajectories
                reference = np.genfromtxt(reference_filename, delimiter=',', names=True, deletechars='')
            else:
                reference = None

            plot_filename = os.path.join(fmu_result_dir, 'result.png')
            plot_result(result, reference, filename=plot_filename)

            with open(os.path.join(fmu_result_dir, 'ReadMe.txt'), 'w') as f:
                f.write("See FMPy documentation for how to run simulate FMUs\n")

            html.write(r'<td><div class="tooltip">' + res_cell + '<span class="tooltiptext"><img src="'
                       + os.path.join(model_path, 'result.png').replace('\\', '/') + '"/></span ></div></td>')
        else:
            plot_filename = None
            html.write('<td class="status">' + res_cell + '</td>\n')

        html.write('</tr>\n')

    html.write('</table></body></html>')

    print("Done.")
