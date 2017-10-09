from .simulation import simulate_fmu
from .util import plot_result, read_csv, write_csv
import argparse
import textwrap


description = """\
Simulate an FMU

Example: 
    > python -m fmpy.simulate Rectifier.fmu
    
"""

parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description=textwrap.dedent(description))

parser.add_argument('fmu_filename', help="filename of the FMU to simulate")
parser.add_argument('--solver', choices=['Euler', 'CVode'], default='CVode', help="solver to use for Model Exchange")
parser.add_argument('--input-file', help="CSV file to use as input")
parser.add_argument('--output-file', help="CSV to store the results")
parser.add_argument('--num-samples', default=500, type=int, help="number of samples to record")
parser.add_argument('--step-size', type=float, help="step size for fixed-step solvers")
parser.add_argument('--start-time', type=float, help="start time for the simulation")
parser.add_argument('--stop-time', type=float, help="stop time for the simulation")
parser.add_argument('--show-plot', action='store_true', help="plot the results")
parser.add_argument('--timeout', type=float, help="max. time to wait for the simulation to finish")
parser.add_argument('--fmi-logging', action='store_true', help="enable FMI logging")

args = parser.parse_args()


if __name__ == '__main__':

    if args.input_file:
        input = read_csv(args.input_file)
    else:
        input = None

    result = simulate_fmu(args.fmu_filename,
                          validate=True,
                          start_time=args.start_time,
                          stop_time=args.stop_time,
                          solver=args.solver,
                          step_size=args.step_size,
                          sample_interval=None,
                          fmi_type=None,
                          start_values={},
                          input=input,
                          output=None,
                          timeout=args.timeout,
                          fmi_logging=args.fmi_logging)

    if args.output_file:
        write_csv(args.output_file, result)

    if args.show_plot:
        plot_result(result=result, window_title=args.fmu_filename)
