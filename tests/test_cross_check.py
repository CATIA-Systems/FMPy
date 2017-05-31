import os
import numpy as np

import fmpy

from fmpy.cc import check_exported_fmu


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
