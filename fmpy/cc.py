import os
import numpy as np
from . import read_model_description


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

        if file.endswith('_in.csv'):
            input_filename = file

        if file.endswith('_ref.csv'):
            reference_filename = file

        if file.endswith('_cc.bat'):
            batch_filename = file

    # read the model description
    try:
        model_description = read_model_description(os.path.join(test_fmu_dir, fmu_filename))
        xml = None
    except Exception as e:
        # try again without validation
        model_description = read_model_description(os.path.join(test_fmu_dir, fmu_filename), validate=False)
        xml = str(e)

    input_variables = []
    output_variables = []

    # collect the variable names
    for variable in model_description.modelVariables:
        if variable.causality == 'input':
            input_variables.append(variable.name)
        elif variable.causality == 'output':
            output_variables.append(variable.name)

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

    #m2 = check_csv_file(os.path.join(test_fmu_dir, input_filename), model_description, is_input=True)

    return xml, in_csv, ref_csv, cc_csv
