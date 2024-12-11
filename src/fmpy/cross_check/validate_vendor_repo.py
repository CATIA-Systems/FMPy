from __future__ import print_function

import sys
import os
import numpy as np
import shutil

from fmpy import read_model_description
from fmpy.cross_check import validate_result
from fmpy.util import read_ref_opt_file


def read_csv(filename, variable_names=None):
    """ Read a CSV file that conforms to the FMI cross-check rules

    Parameters:
        filename         name of the CSV file to read
        variable_names   list of legal variable names

    Returns:
        traj             the trajectoies read from the CSV file
    """

    # pass an empty string as deletechars to preserve special characters
    traj = np.genfromtxt(filename, delimiter=',', names=True, deletechars='')

    # get the time
    time = traj[traj.dtype.names[0]]

    # check if the time is monotonically increasing
    if traj.size > 1 and np.any(np.diff(time) < 0):
        raise Exception("Values in first column (time) are not monotonically increasing")

    # check if all variables exist in the FMU
    if variable_names is not None:
        for name in traj.dtype.names[1:]:
            if name not in variable_names:
                raise Exception("Variable '%s' does not exist in the FMU" % name)

    return traj


def validate_test_fmu(model_dir):
    """ Validate an exported FMU

    Parameters:
        model_dir  path to the directory that contains the exported FMU

    Returns:
        a list of problems
    """

    problems = []

    # check file sizes
    for root, dirs, files in os.walk(model_dir):
        for file in files:
            filename = os.path.join(root, file)
            filesize = os.path.getsize(filename)
            maxsize = 10e6 if file.endswith('.fmu') else 1e6
            if filesize > maxsize:
                problems.append("%s is larger than %g MB (%g MB)" % (filename, maxsize * 1e-6, filesize * 1e-6))

    if 'notCompliantWithLatestRules' in files:
        return problems  # stop here

    path, model_name = os.path.split(model_dir)
    path, _ = os.path.split(path)
    path, _ = os.path.split(path)
    path, platform = os.path.split(path)
    path, fmi_type = os.path.split(path)
    _, fmi_version = os.path.split(path)

    fmu_filename = os.path.join(model_dir, model_name + '.fmu')

    # validate the modelDescription.xml
    try:
        model_description = read_model_description(fmu_filename, validate=True)
    except Exception as e:
        problems.append("Error in %s. %s" % (fmu_filename, e))
        return problems  # stop here

    # check FMI version
    if model_description.fmiVersion != fmi_version:
        problems.append("%s is not an FMI %s FMU" % (fmu_filename, fmi_version))
        return problems  # stop here

    # check FMI type
    if fmi_type == 'cs' and model_description.coSimulation is None:
        problems.append("%s does not support co-simulation" % fmu_filename)
        return problems  # stop here
    elif fmi_type == 'me' and model_description.modelExchange is None:
        problems.append("%s does not support model-exchange" % fmu_filename)
        return problems  # stop here

    # collect the variable names
    variable_names = [v.name for v in model_description.modelVariables]

    # check the reference options file
    try:
        ref_opts_filename = os.path.join(model_dir, model_name + '_ref.opt')
        read_ref_opt_file(ref_opts_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (ref_opts_filename, e))

    # check the CSVs
    for suffix, required in [('_in.csv', False), ('_ref.csv', True)]:

        csv_filename = os.path.join(model_dir, model_name + suffix)

        if not required and not os.path.isfile(csv_filename):
            continue

        try:
            read_csv(csv_filename, variable_names=variable_names)
        except Exception as e:
            problems.append("Error in %s. %s" % (csv_filename, e))

    return problems


def validate_cross_check_result(result_dir):
    """ Validate a cross-check result

    Parameters:
        result_dir  path to the directory that contains the results

    Returns:
        a list of problems
    """

    problems = []

    t = segments(result_dir)

    fmi_version, fmi_type, platform, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name = t[-8:]

    repo_dir = os.path.join(*t[:-9])

    fmu_dir = os.path.join(repo_dir, 'fmus', fmi_version, fmi_type, platform, exporting_tool_name, exporting_tool_version, model_name)

    ref_filename = os.path.join(fmu_dir, model_name + '_ref.csv')
    opt_filename = os.path.join(fmu_dir, model_name + '_ref.opt')

    # check file sizes
    for root, dirs, files in os.walk(result_dir):
        for file in files:
            filename = os.path.join(root, file)
            filesize = os.path.getsize(filename)
            if filesize > 1e6:
                problems.append("%s is larger than 1 MB (%.1f MB)" % (filename, filesize * 1e-6))

    _, model_name = os.path.split(result_dir)

    not_compliant_file = os.path.join(result_dir, 'notCompliantWithLatestRules')
    passed_file = os.path.join(result_dir, 'passed')

    if os.path.isfile(not_compliant_file) or not os.path.isfile(passed_file):
        return problems  # stop here

    # check the output file
    res_filename = os.path.join(result_dir, model_name + '_out.csv')

    try:
        result = read_csv(res_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (res_filename, e))
        return problems  # stop here

    try:
        reference = read_csv(ref_filename)
        opt = read_ref_opt_file(opt_filename)
    except Exception as e:
        problems.append("Error in %s. %s" % (res_filename, e))
        return problems  # stop here

    problem = validate_result(result=result, reference=reference, t_start=opt['StartTime'], t_stop=opt['StopTime'])

    if problem is not None:
        problems.append("Error in %s. %s" % (res_filename, problem))

    return problems


def segments(path):
    """ Split a path into segments """

    s = []

    head, tail = os.path.split(path)

    while tail:
        s.insert(0, tail)
        head, tail = os.path.split(head)

    s.insert(0, head)

    return s


def validate_repo(vendor_dir, clean_up=False):

    problems = []

    s = segments(vendor_dir)

    result_count = 0

    # validate the cross-check results
    for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'results')):

        t = segments(subdir)

        if len(t) - len(s) != 9:
            continue

        result_count += 1

        fmi_version, fmi_type, platform, importing_tool_name, importing_tool_version, exporting_tool_name, exporting_tool_version, model_name = t[-8:]

        if fmi_version not in ['1.0', '2.0']:
            continue

        if fmi_type not in ['cs', 'me']:
            continue

        if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
            continue

        new_problems = validate_cross_check_result(subdir)

        if new_problems and clean_up:
            passed_file = os.path.join(subdir, 'passed')
            if os.path.isfile(passed_file):
                print("Removing %s" % passed_file)
                os.remove(passed_file)

        problems += new_problems

    fmu_count = 0

    # validate the test FMUs
    for subdir, dirs, files in os.walk(os.path.join(vendor_dir, 'fmus')):

        t = segments(subdir)

        if len(t) - len(s) != 7:
            continue

        fmu_count += 1

        fmi_version, fmi_type, platform, tool_name, tool_version, model_name = t[-6:]

        if fmi_version not in ['1.0', '2.0']:
            continue

        if fmi_type not in ['cs', 'me']:
            continue

        if platform not in ['c-code', 'darwin64', 'linux32', 'linux64', 'win32', 'win64']:
            continue

        new_problems = validate_test_fmu(subdir)

        if new_problems and clean_up:
            not_compliant_file = os.path.join(subdir, 'notCompliantWithLatestRules')
            print("Adding %s" % not_compliant_file)
            with open(not_compliant_file, 'a'):
                pass

        problems += new_problems

    return fmu_count, result_count, problems


if __name__ == '__main__':

    import argparse
    import textwrap

    description = """\
    Validate cross-check results and test FMUs in vendor repositories 
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(description))

    parser.add_argument('xc_repo', default=os.getcwd(), nargs='?', help="path to the vendor repository")
    parser.add_argument('--clean-up', action='store_true', help="remove 'passed' or add 'notCompliantWithLatestRules' file")

    args = parser.parse_args()

    fmu_count, result_count, problems = validate_repo(args.xc_repo, args.clean_up)

    print()
    print("#################################")
    print("%d problems found in %s" % (len(problems), args.xc_repo))
    print("Validated %d FMUs and %d results" % (fmu_count, result_count))
    print("#################################")
    print()

    for problem in problems:
        print()
        print(problem)

    sys.exit(len(problems))
