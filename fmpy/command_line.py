""" Command line interface for FMPy """


def main():

    import argparse
    import textwrap

    description = """\
    Validate and simulate Functional Mock-up Units (FMUs)

    Get information about an FMU:
       
        fmpy info Rectifier.fmu
     
    Simulate an FMU:
     
        fmpy simulate Rectifier.fmu --show-plot
        
    Compile a source code FMU:
    
        fmpy compile Rectifier.fmu
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(description))

    parser.add_argument('command', choices=['info', 'simulate', 'compile'], help="Command to execute")
    parser.add_argument('fmu_filename', help="filename of the FMU")

    parser.add_argument('--solver', choices=['Euler', 'CVode'], default='CVode',
                        help="solver to use for Model Exchange")
    parser.add_argument('--input-file', help="CSV file to use as input")
    parser.add_argument('--output-variables', nargs='+', help="Variables to record")
    parser.add_argument('--output-file', help="CSV to store the results")
    parser.add_argument('--num-samples', default=500, type=int, help="number of samples to record")
    parser.add_argument('--step-size', type=float, help="step size for fixed-step solvers")
    parser.add_argument('--start-time', type=float, help="start time for the simulation")
    parser.add_argument('--stop-time', type=float, help="stop time for the simulation")
    parser.add_argument('--show-plot', action='store_true', help="plot the results")
    parser.add_argument('--timeout', type=float, help="max. time to wait for the simulation to finish")
    parser.add_argument('--fmi-logging', action='store_true', help="enable FMI logging")
    parser.add_argument('--start-values', nargs='+', help="name-value pairs of start values")

    args = parser.parse_args()

    if args.command == 'info':

        from fmpy import dump
        dump(args.fmu_filename)

    elif args.command == 'compile':

        from fmpy.util import compile_platform_binary
        compile_platform_binary(args.fmu_filename)

    elif args.command == 'simulate':

        from fmpy import simulate_fmu
        from fmpy.util import read_csv, write_csv, plot_result

        if args.start_values:
            if len(args.start_values) % 2 != 0:
                raise Exception("Start values must be name-value pairs.")
            start_values = {k: v for k, v in zip(args.start_values[::2], args.start_values[1::2])}
        else:
            start_values = {}

        input = read_csv(args.input_file) if args.input_file else None

        result = simulate_fmu(args.fmu_filename,
                              validate=True,
                              start_time=args.start_time,
                              stop_time=args.stop_time,
                              solver=args.solver,
                              step_size=args.step_size,
                              output_interval=None,
                              fmi_type=None,
                              start_values=start_values,
                              input=input,
                              output=args.output_variables,
                              timeout=args.timeout,
                              fmi_logging=args.fmi_logging)

        if args.output_file:
            write_csv(filename=args.output_file, result=result)

        if args.show_plot:
            plot_result(result=result, window_title=args.fmu_filename)
