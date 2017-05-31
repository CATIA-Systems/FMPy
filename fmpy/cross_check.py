import os
import numpy as np
import sys
import fmpy

def check_csv_file(file_path, variable_names):

    # read the trajectories
    try:
        traj = np.genfromtxt(file_path, delimiter=',', names=True)
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

    # check if the trajectory names match the variable names
    for traj_name in traj_names:
        if traj_name not in variable_names:
            return "Trajectory '" + traj_name + "' does not match any variable name"

    # check if the variable names match the trajectory names
    for variable_name in variable_names:
        if variable_name not in traj_names:
            return "Variable '" + variable_name + "' does not match any trajectory name"

    return None


def check_exported_fmu(test_fmu_dir):

    for file in os.listdir(test_fmu_dir):

        if file.endswith('.fmu'):
            fmu_filename = file
            fmu_name, _ = os.path.splitext(fmu_filename)

        # if file.endswith('_in.csv'):
        #     input_filename = file
        #
        # if file.endswith('_ref.csv'):
        #     reference_filename = file
        #
        # if file.endswith('_cc.bat'):
        #     batch_filename = file

    # read the model description
    try:
        model_description = fmpy.read_model_description(os.path.join(test_fmu_dir, fmu_filename))
        xml = None
    except Exception as e:
        # try again without validation
        model_description = fmpy.read_model_description(os.path.join(test_fmu_dir, fmu_filename), validate=False)
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
    except Exception as e:
        ref_opt = str(e)

    # check reference file
    ref_path = os.path.join(test_fmu_dir, fmu_name + '_ref.csv')
    ref_csv = check_csv_file(ref_path, output_variables)

    # check reference file
    cc_path = os.path.join(test_fmu_dir, fmu_name + '_cc.csv')
    cc_csv = check_csv_file(cc_path, output_variables)

    # check input file
    if input_variables:
        in_path = os.path.join(test_fmu_dir, fmu_name + '_in.csv')
        in_csv = check_csv_file(in_path, input_variables)
    else:
        in_csv = None

    return xml, ref_opt, in_csv, ref_csv, cc_csv


def read_ref_opt_file(filename):

    opts = {}

    with open(filename, 'r') as f:
        for line in f:
            segments = line.split(',')
            if len(segments) == 2:
                opts[segments[0]] = float(segments[1])

    for element in ['StepSize', 'StartTime', 'StopTime', 'RelTol']:
        if not element in opts:
            raise Exception("Missing element '%s'" % element)

    return opts


if __name__ == '__main__':
    """ Usage: python -m fmpy.cross_check <test_fmu_dir> """

    if len(sys.argv) > 1:
        testFMUsDirectory = sys.argv[1]
    else:
        testFMUsDirectory = os.getcwd()

    fmiVersions = ['fmi1', 'fmi2']
    fmiTypes = ['me', 'cs']
    platforms = ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']
    tools = None
    models = None

    html = open('report.html', 'w')
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
    html.write('<tr><th>Model</th><th>XML</th><th>_ref.opt</th><th>_in.csv</th><th>_cc.csv</th><th>_ref.csv</th><th>simulation</th></tr>\n')

    for fmiVersion in fmiVersions:

        for fmiType in fmiTypes:

            for platform in platforms:

                platformDir = os.path.join(testFMUsDirectory,
                                           'FMI_1.0' if fmiVersion == 'fmi1' else 'FMI_2.0',
                                           'ModelExchange' if fmiType == 'me' else 'CoSimulation',
                                           platform)

                if not os.path.isdir(platformDir):
                    continue

                for tool in os.listdir(platformDir):

                    if tools is not None and not tool in tools:
                        continue

                    if tool == 'AMESim':
                        continue

                    toolDir = os.path.join(platformDir, tool)

                    if not os.path.isdir(toolDir):
                        continue

                    versions = os.listdir(toolDir)
                    version = sorted(versions)[-1] # take only the latest version
                    versionDir = os.path.join(toolDir, version)

                    for model in os.listdir(versionDir):

                        if models is not None and model not in models:
                            continue

                        modelDir = os.path.join(versionDir, model)

                        if not os.path.isdir(modelDir):
                            continue

                        test_fmu_dir = os.path.join('FMI_1.0' if fmiVersion == 'fmi1' else 'FMI_2.0',
                                                          'ModelExchange' if fmiType == 'me' else 'CoSimulation',
                                                          platform, tool, version, model)

                        print(test_fmu_dir)

                        modelPath = 'modelPath'

                        xml, ref_opt, in_csv, ref_csv, cc_csv = check_exported_fmu(os.path.join(testFMUsDirectory, test_fmu_dir))

                        sim_cell = '<td class="status"><span class="label label-default">skipped</span></td>'

                        if ref_opt is None and platform == fmpy.platform:

                            # find the FMU
                            for file in os.listdir(os.path.join(testFMUsDirectory, test_fmu_dir)):
                                if file.endswith('.fmu'):
                                    fmu_filename = file
                                    fmu_name, _ = os.path.splitext(fmu_filename)

                            ref_opts = read_ref_opt_file(os.path.join(testFMUsDirectory, test_fmu_dir, fmu_name + '_ref.opt'))

                            print("Simulating " + fmu_filename)
                            fmu = os.path.join(testFMUsDirectory, test_fmu_dir, fmu_filename)
                            try:
                                result = fmpy.simulate_fmu(filename=fmu, validate=False, step_size=ref_opts['StepSize'], stop_time=ref_opts['StepSize'])
                                print("done.")
                                sim_cell = '<td class="status"><span class="label label-success">passed</span></td>'
                            except Exception as e:
                                print("failed.")
                                sim_cell =  '<td class="status"><span class="label label-danger" title="' + str(e) + '">failed</span></td>'

                        def cell(text):
                            if text is not None:
                                return '<td class="status"><span class="label label-danger" title="' + text + '">failed</span></td>'
                            else:
                                return '<td class="status"><span class="label label-success">passed</span></td>'

                        html.write('<tr><td>' + test_fmu_dir + '</td>')
                        html.write(cell(xml))
                        html.write(cell(ref_opt))
                        html.write(cell(in_csv))
                        html.write(cell(ref_csv))
                        html.write(cell(cc_csv))
                        html.write(sim_cell)
                        html.write('</tr>\n')

    html.write('</table></body></html>')
