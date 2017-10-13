import fmpy
import zipfile
import time
from ..util import *


def cross_check(fmus_dir, report, result_dir, simulate, tool_name, tool_version, skip, readme):

    html = open(report, 'w')
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

    for root, dirs, files in os.walk(fmus_dir):

        fmu_filename = None

        for file in files:
            if file.endswith('.fmu'):
                fmu_name, _ = os.path.splitext(file)  # FMU name without file extension
                fmu_filename = os.path.join(root, file)  # absolute path filename
                break

        if fmu_filename is None:
            continue

        # dictionary that contains the information about the FMU
        options = {'fmu_filename': fmu_filename}

        # extract the cross-check info from the path
        options.update(fmu_path_info(root))

        # skip FMUs in _FMIModelicaTest and other directories
        if options['fmi_version'] not in ['FMI_1.0', 'FMI_2.0']:
            continue

        if skip(options):
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
            in_path = None
            in_csv_cell = '<td class="status"><span class="label label-default">n/a</span></td>'

        # check the reference file
        ref_path = os.path.join(root, fmu_name + '_ref.csv')
        reference, ref_csv_cell = check_csv_file(filename=ref_path, variables=output_variables)

        # supported_platforms = fmpy.supported_platforms(fmu_filename)

        # this will remove any trailing (back)slashes
        fmus_dir = os.path.normpath(fmus_dir)
        model_path = fmu_filename[len(fmus_dir) + 1:]
        model_path = os.path.dirname(model_path)
        fmu_simple_filename = os.path.basename(fmu_filename)
        model_name, _ = os.path.splitext(fmu_simple_filename)

        # build the filenames
        result = None

        ##############
        # SIMULATION #
        ##############

        skipped = True

        if simulate is None:
            sim_cell = '<td class="status" title="Simulation is disabled"><span class="label label-default">skipped</span></td>'
        elif ref_opts is None:
            sim_cell = '<td class="status" title="Failed to read *_ref.opt file"><span class="label label-default">skipped</span></td>'
        elif input_variables and input is None:
            sim_cell = '<td class="status" title="Input file is invalid"><span class="label label-default">skipped</span></td>'
        else:
            skipped = False

            step_size = ref_opts['StepSize']
            stop_time = ref_opts['StopTime']

            if reference is not None:
                output_variable_names = reference.dtype.names[1:]
            else:
                output_variable_names = None

            try:
                start_time = time.time()

                options['fmu_filename'] = fmu_filename
                options['step_size'] = step_size
                options['stop_time'] = stop_time

                if in_path is not None:
                    options['input_filename'] = in_path

                options['output_variable_names'] = output_variable_names

                # simulate the FMU
                result = simulate(options)

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
        fmus_dir = os.path.normpath(fmus_dir)

        model_path = fmu_filename[len(fmus_dir)+1:]

        model_path = os.path.dirname(model_path)

        html.write('<tr><td>' + root + '</td>')
        html.write('\n'.join([xml_cell, ref_opts_cell, in_csv_cell, ref_csv_cell, doc_cell, sim_cell]))

        if result_dir is not None and result is not None:

            relative_result_dir = os.path.join(result_dir, options['fmi_version'], options['fmi_type'],
                                               options['platform'], tool_name, tool_version, options['tool_name'],
                                               options['tool_version'], options['model_name'])

            fmu_result_dir = os.path.join(result_dir, relative_result_dir)

            if not os.path.exists(fmu_result_dir):
                os.makedirs(fmu_result_dir)

            # write the indicator file
            if skipped:
                indicator_filename = 'rejected'
            elif rel_out < 0.1:
                indicator_filename = 'passed'
            else:
                indicator_filename = 'failed'

            with open(os.path.join(fmu_result_dir, indicator_filename), 'w') as f:
                pass

            if readme is not None:
                # write the ReadMe.txt file
                with open(os.path.join(fmu_result_dir, 'ReadMe.txt'), 'w') as f:
                    f.write(readme())

            result_filename = os.path.join(fmu_result_dir, model_name + '_out.csv')

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

            html.write(r'<td><div class="tooltip">' + res_cell + '<span class="tooltiptext"><img src="'
                       + os.path.join(relative_result_dir, 'result.png').replace('\\', '/') + '"/></span ></div></td>')
        else:
            html.write('<td class="status">' + res_cell + '</td>\n')

        html.write('</tr>\n')

    html.write('</table></body></html>')

    print("Done.")
