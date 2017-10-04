import argparse
import os
import fmpy
from fmpy.cross_check.utilities import read_csv
from fmpy.cross_check.cross_check import cross_check

parser = argparse.ArgumentParser(description='run the FMI cross-check')

parser.add_argument('--fmus_dir', default=os.getcwd(), help='the directory that contains the test FMUs')
parser.add_argument('--report', default='report.html', help='name of the report file')
parser.add_argument('--result_dir', help='the directory to store the results')
parser.add_argument('--include', nargs='+', default=[], help='path segments to include')
parser.add_argument('--exclude', nargs='+', default=[], help='path segments to exclude')
parser.add_argument('--simulate', action='store_true', help='simulate the FMU')

# parse the command line arguments
args = parser.parse_args()


def skip(options):

    fmu_filename = options['fmu_filename']

    # skip all models that match any of the exclude patterns
    for pattern in args.exclude:
        if pattern in fmu_filename:
            return True

    # only include models that match all include patterns
    for pattern in args.include:
        if pattern not in fmu_filename:
            return True

    # Sort out the FMUs that crash the process

    # fullRobot w/ ModelExchange
    if 'ModelExchange' in fmu_filename and 'fullRobot' in fmu_filename:
        return True  # cannot be solved w/ Euler

    # win64
    if r'FMI_2.0\CoSimulation\win64\AMESim\15\MIS_cs' in fmu_filename:
        return True  # exitInitializationMode() does not return in release mode

    # linux64
    if 'FMI_1.0/ModelExchange/linux64/JModelica.org/1.15' in fmu_filename:
        return True  # exit code 139 (interrupted by signal 11: SIGSEGV)

    if 'FMI_1.0/ModelExchange/linux64/AMESim' in fmu_filename:
        return True  # exit code 139 (interrupted by signal 11: SIGSEGV)

    return False


def simulate(options):

    # read the input file
    if 'input_filename' in options:
        input = read_csv(options['input_filename'])
    else:
        input = None

    step_size = options['step_size']

    if step_size == 0:
        step_size = None

    # simulate the FMU
    result = fmpy.simulate_fmu(filename=options['fmu_filename'], validate=False, step_size=step_size,
                               stop_time=options['stop_time'], input=input, output=options['output_variable_names'])

    return result


cross_check(args.fmus_dir, args.report, args.result_dir, simulate, 'FMPy', fmpy.__version__, skip)
