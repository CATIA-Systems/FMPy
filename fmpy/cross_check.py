import os
import numpy as np
import fmpy

def check_csv_file(file_path, variable_names):

    try:
        # pass an empty string as deletechars to preserve special characters
        traj = np.genfromtxt(file_path, delimiter=',', names=True, deletechars='')
    except:
        return "Failed to read CSV"

    if traj.dtype.names[0] != 'time':
        return "First column should be 'time' but was '%s'" % traj.dtype.names[0]

    # get the time
    time = traj['time']

    # check if the time is monotonically increasing
    if np.any(np.diff(time) < 0):
        return "Values in first column (time) are not monotonically increasing"

    # get the trajectory names (without the time)
    traj_names = traj.dtype.names[1:]

    # # check if the trajectory names match the variable names
    # for traj_name in traj_names:
    #     if traj_name not in variable_names:
    #         return "Trajectory '" + traj_name + "' does not match any variable name"

    # check if the variable names match the trajectory names
    for variable_name in variable_names:
        if variable_name not in traj_names:
            return "Trajectory of '" + variable_name + "' is missing"

    return None


def check_exported_fmu(fmu_filename):

    test_fmu_dir, fmu_name_ = os.path.split(fmu_filename)

    for file in os.listdir(test_fmu_dir):
        if file.endswith('.fmu'):
            fmu_name, _ = os.path.splitext(file)
            break

    # read the model description
    try:
        model_description = fmpy.read_model_description(fmu_filename)
        xml = None
    except Exception as e:
        # try again without validation
        model_description = fmpy.read_model_description(fmu_filename, validate=False)
        xml = str(e)

    input_variables = []
    output_variables = []

    # collect the variable names
    for variable in model_description.modelVariables:
        if variable.causality == 'input':
            input_variables.append(variable.name)
        elif variable.causality == 'output':
            output_variables.append(variable.name)

    # check the options file
    try:
        ref_opts = read_ref_opt_file(os.path.join(test_fmu_dir, fmu_name + '_ref.opt'))
        ref_opt = None

        # if 'CoSimulation' in test_fmu_dir and ref_opts['StepSize'] == 0.0:
        #     ref_opt = "Co-simulation FMU is requesting variable-step solver"
    except Exception as e:
        ref_opt = str(e)

    # check the input file
    if input_variables:
        in_path = os.path.join(test_fmu_dir, fmu_name + '_in.csv')
        in_csv = check_csv_file(in_path, input_variables)
    else:
        in_csv = None

    # check the reference file
    ref_path = os.path.join(test_fmu_dir, fmu_name + '_ref.csv')
    ref_csv = check_csv_file(ref_path, output_variables)

    # check the compliance checker file
    cc_path = os.path.join(test_fmu_dir, fmu_name + '_cc.csv')
    cc_csv = check_csv_file(cc_path, output_variables)

    return xml, ref_opt, in_csv, ref_csv, cc_csv


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


def plot_result(result, reference=None, filename=None):

    import matplotlib.pylab as pylab
    import matplotlib.pyplot as plt
    from collections import Iterable

    params = {
            # 'legend.fontsize': 'medium',
            #'figure.figsize': (10, 8),
            'legend.fontsize': 'small',
            'axes.labelsize': 'small',
            #   'axes.titlesize': 'medium',
            'xtick.labelsize': 'small',
            'ytick.labelsize': 'small'
    }

    pylab.rcParams.update(params)

    time = result['time']
    names = result.dtype.names[1:]

    if len(names) > 0:

        fig, axes = plt.subplots(len(names), sharex=True)

        fig.set_facecolor('white')

        if not isinstance(axes, Iterable):
            axes = [axes]

        for ax, name in zip(axes, names):

            ax.grid(b=True, which='both', color='0.8', linestyle='-', zorder=0)

            if reference is not None and name in reference.dtype.names:
                t_ref = reference[reference.dtype.names[0]]
                y_ref = reference[name]
                ax.plot(t_ref, y_ref, color=(1, 0.5, 0.5), linewidth=5, label='result', zorder=101)

            ax.plot(time, result[name], 'b', label='result', zorder=101)

            ax.set_ylabel(name)

            ax.margins(x=0, y=0.1)

        if reference is not None:
            #ax.legend()
            plt.legend(bbox_to_anchor=(0, -0.4, 1., 0.1), loc=8, ncol=2, mode="normal", borderaxespad=0.5)


        fig.set_size_inches(w=12, h=8, forward=True)
        plt.tight_layout()
        fig.subplots_adjust(bottom=0.08)

        if filename is None:
            plt.show()
        else:
            dir, file = os.path.split(filename)
            if not os.path.isdir(dir):
                os.makedirs(dir)
            fig.savefig(filename=filename)


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
                display: inline;
                padding: .2em .6em .3em;
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

            .label-success {
                background-color: #5cb85c;
            }

            .label-default {
                background-color: #777;
            }
        </style>
    </head>
    <body>
        <table>''')
    html.write('<tr><th>Model</th><th>XML</th><th>_ref.opt</th><th>_in.csv</th><th>_ref.csv</th><th>_cc.csv</th><th>simulation</th><th></th><th></th></tr>\n')

    for root, dirs, files in os.walk(args.fmus_dir):

        fmu_filename = None

        for file in files:
            if file.endswith('.fmu'):
                fmu_filename = os.path.join(root, file)
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

            # AMESim MIS_cs does not return from exitInitializationMode()
            if 'MIS_cs' in fmu_filename:
                return True

            # FMIToolbox_MATLAB FMUs get stuck in release mode
            if 'FMIToolbox_MATLAB' in fmu_filename:
                return True

            return False

        if skip(include=args.include, exclude=args.exclude):
            continue

        platformDir = root
        print(platformDir)

        xml, ref_opt, in_csv, ref_csv, cc_csv = check_exported_fmu(fmu_filename)

        supported_platforms = fmpy.supported_platforms(fmu_filename)

        result = None

        if not args.simulate:
            sim_cell = '<td class="status" title="Simulation is disabled"><span class="label label-default">skipped</span></td>'
        elif ref_opt is not None:
            sim_cell = '<td class="status" title="Failed to read *_ref.opt file"><span class="label label-default">skipped</span></td>'
        elif in_csv is not None:
            sim_cell = '<td class="status" title="Input file is invalid"><span class="label label-default">skipped</span></td>'
        elif fmpy.platform not in supported_platforms:
            sim_cell = '<td class="status" title="The current platform (' + fmpy.platform + ') is not supported by the FMU (' + ', '.join(supported_platforms) + ')"><span class="label label-default">skipped</span></td>'
        else:
            fmu_simple_filename = os.path.basename(fmu_filename)
            model_name, _ = os.path.splitext(fmu_simple_filename)

            # read the reference options
            ref_opts = read_ref_opt_file(os.path.join(root, model_name + '_ref.opt'))

            # read the input
            input_filename = os.path.join(root, model_name + '_in.csv')

            if os.path.isfile(input_filename):
                input = np.genfromtxt(input_filename, delimiter=',', names=True, deletechars='')
            else:
                input = None

            step_size = ref_opts['StepSize']

            # variable step solvers are currently not supported
            if step_size == 0:
                step_size = None

            try:
                # simulate the FMU
                result = fmpy.simulate_fmu(filename=fmu_filename, validate=False, step_size=step_size, stop_time=ref_opts['StopTime'], input=input)
                sim_cell = '<td class="status"><span class="label label-success">passed</span></td>'
            except Exception as e:
                sim_cell =  '<td class="status"><span class="label label-danger" title="' + str(e) + '">failed</span></td>'

        def cell(text):
            if text is not None:
                return '<td class="status"><span class="label label-danger" title="' + text + '">failed</span></td>'
            else:
                return '<td class="status"><span class="label label-success">passed</span></td>'

        html.write('<tr><td>' + root + '</td>')
        html.write(cell(xml))
        html.write(cell(ref_opt))
        html.write(cell(in_csv))
        html.write(cell(ref_csv))
        html.write(cell(cc_csv))
        html.write(sim_cell)

        # this will remove any trailing (back)slashes
        fmus_dir = os.path.normpath(args.fmus_dir)

        model_path = fmu_filename[len(fmus_dir)+1:]

        model_path = os.path.dirname(model_path)

        if args.result_dir is not None and result is not None:

            fmu_result_dir = os.path.join(args.result_dir, model_path)

            if not os.path.exists(fmu_result_dir):
                 os.makedirs(fmu_result_dir)

            header = ','.join(map(lambda s: '"' + s + '"', result.dtype.names))
            result_filename = os.path.join(fmu_result_dir, 'result.csv')
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

            html.write('<td><a href="file://' + result_filename + '">result.csv</td>\n')
            html.write('<td><a href="file://' + plot_filename + '">result.png</td>\n')

        else:
            html.write('<td></td>\n')
            html.write('<td></td>\n')

        html.write('</tr>\n')

    html.write('</table></body></html>')

    print("Done.")
