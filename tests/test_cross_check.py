import os
import numpy as np

import fmpy

from fmpy import read_model_description
from fmpy.cc import check_csv_file
from fmpy.cc import check_exported_fmu

# def check_csv_file(file_path, variable_names):
#
#     # read the trajectories
#     try:
#         traj = np.genfromtxt(file_path, delimiter=',', names=True)
#     except:
#         return "Failed to read CSV"
#
#     if traj.dtype.names[0] != 'time':
#         return "First column should be 'time' but was '%s'" % traj.dtype.names[0]
#
#     # get the time
#     time = traj['time']
#
#     # check if the time is monotonically increasing
#     if np.any(np.diff(time) < 0):
#         return "Values in first column (time) are not monotonically increasing"
#
#     # get the trajectory names (without the time)
#     traj_names = traj.dtype.names[1:]
#
#     # check if the trajectory names match the variable names
#     for traj_name in traj_names:
#         if traj_name not in variable_names:
#             return "Trajectory '" + traj_name + "' does not match any variable name"
#
#     # check if the variable names match the trajectory names
#     for variable_name in variable_names:
#         if variable_name not in traj_names:
#             return "Variable '" + variable_name + "' does not match any trajectory name"
#
#     return None


# def check_exported_fmu(test_fmu_dir):
#
#     for file in os.listdir(test_fmu_dir):
#
#         if file.endswith('.fmu'):
#             fmu_filename = file
#             fmu_name, _ = os.path.splitext(fmu_filename)
#
#         if file.endswith('_in.csv'):
#             input_filename = file
#
#         if file.endswith('_ref.csv'):
#             reference_filename = file
#
#         if file.endswith('_cc.bat'):
#             batch_filename = file
#
#     # read the model description
#     try:
#         model_description = read_model_description(os.path.join(test_fmu_dir, fmu_filename))
#         xml = None
#     except Exception as e:
#         # try again without validation
#         model_description = read_model_description(os.path.join(test_fmu_dir, fmu_filename), validate=False)
#         xml = str(e)
#
#     input_variables = []
#     output_variables = []
#
#     # collect the variable names
#     for variable in model_description.modelVariables:
#         if variable.causality == 'input':
#             input_variables.append(variable.name)
#         elif variable.causality == 'output':
#             output_variables.append(variable.name)
#
#     # check reference file
#     ref_path = os.path.join(test_fmu_dir, fmu_name + '_ref.csv')
#     ref_csv = check_csv_file(ref_path, output_variables)
#
#     # check reference file
#     cc_path = os.path.join(test_fmu_dir, fmu_name + '_cc.csv')
#     cc_csv = check_csv_file(cc_path, output_variables)
#
#     # check input file
#     if input_variables:
#         in_path = os.path.join(test_fmu_dir, fmu_name + '_in.csv')
#         in_csv = check_csv_file(in_path, input_variables)
#     else:
#         in_csv = None
#
#     #m2 = check_csv_file(os.path.join(test_fmu_dir, input_filename), model_description, is_input=True)
#
#     return xml, in_csv, ref_csv, cc_csv


if __name__ == '__main__':

    testFMUsDirectory = r'Z:\Development\FMI\branches\public\Test_FMUs'
    # reportDir = os.environ['REPORT_DIR']

    fmiVersions = ['fmi1', 'fmi2']
    fmiTypes = ['me', 'cs']
    tools = None # ['AMESim'] # ['Dymola']
    models = None # ['ClassEAmplifier']

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
        </style>
    </head>
    <body>
        <table>''')
    html.write('<tr><th>Model</th><th>XML</th><th>_in.csv</th><th>_cc.csv</th><th>_ref.csv</th></tr>\n')

    for fmiVersion in fmiVersions:

        for fmiType in fmiTypes:

            platformDir = os.path.join(testFMUsDirectory,
                                       'FMI_1.0' if fmiVersion == 'fmi1' else 'FMI_2.0',
                                       'ModelExchange' if fmiType == 'me' else 'CoSimulation',
                                       fmpy.platform)

            for tool in os.listdir(platformDir):

                if tools is not None and not tool in tools:
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
                                                       fmpy.platform, tool, version, model)

                    print(test_fmu_dir)

                    modelPath = 'modelPath'

                    xml, in_csv, ref_csv, cc_csv = check_exported_fmu(os.path.join(testFMUsDirectory, test_fmu_dir))

                    def cell(text):
                        if text is not None:
                            return '<td class="status"><span class="label label-danger" title="' + text + '">failed</span></td>'
                            #return '<td class="failed"><span title="' + text + '">FAILED</span></td>'
                        else:
                            #return '<td class="passed">PASSED</td>'
                            return '<td class="status"><span class="label label-success">passed</span></td>'

                    html.write('<tr><td>' + test_fmu_dir + '</td>')
                    html.write(cell(xml))
                    html.write(cell(in_csv))
                    html.write(cell(ref_csv))
                    html.write(cell(cc_csv))
                    html.write('</tr>\n')

    html.write('</table></body></html>')

    pass
