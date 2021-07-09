""" Command line interface for FMPy """

from __future__ import print_function


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
        
    Create a Jupyter Notebook
    
        fmpy create-jupyter-notebook Rectifier.fmu
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description=textwrap.dedent(description))

    parser.add_argument('command', choices=['info', 'validate', 'simulate', 'compile', 'add-cswrapper', 'add-remoting',
                                            'create-cmake-project', 'create-jupyter-notebook'],
                        help="Command to execute")
    parser.add_argument('fmu_filename', help="filename of the FMU")

    parser.add_argument('--validate', action='store_true', help="validate the FMU")
    parser.add_argument('--start-time', type=float, help="start time for the simulation")
    parser.add_argument('--stop-time', type=float, help="stop time for the simulation")
    parser.add_argument('--solver', choices=['Euler', 'CVode'], default='CVode', help="solver to use for Model Exchange")
    parser.add_argument('--step-size', type=float, help="step size for fixed-step solvers")
    parser.add_argument('--relative-tolerance', type=float, help="relative tolerance for the 'CVode' solver and FMI 2.0 co-simulation FMUs")
    parser.add_argument('--dont-record-events', action='store_true', help="dont't record outputs at events (model exchange only)")
    parser.add_argument('--start-values', nargs='+', help="name-value pairs of start values")
    parser.add_argument('--apply-default-start-values', action='store_true', help="apply the start values from the model description")
    parser.add_argument('--output-interval', type=float, help="interval for sampling the output")
    parser.add_argument('--input-file', help="CSV file to use as input")
    parser.add_argument('--output-variables', nargs='+', help="Variables to record")
    parser.add_argument('--output-file', help="CSV to store the results")
    parser.add_argument('--timeout', type=float, help="max. time to wait for the simulation to finish")
    parser.add_argument('--debug-logging', action='store_true', help="enable the FMU's debug logging")
    parser.add_argument('--visible', action='store_true', help="enable interactive mode")
    parser.add_argument('--fmi-logging', action='store_true', help="enable FMI logging")
    parser.add_argument('--show-plot', action='store_true', help="plot the results")
    parser.add_argument('--cmake-project-dir', help="Directory for the CMake project")
    parser.add_argument('--target-platform', help="The target platform to compile the binary for")

    args = parser.parse_args()

    if args.command == 'info':

        from fmpy import dump
        dump(args.fmu_filename)

    elif args.command == 'validate':

        import sys
        from fmpy.validation import validate_fmu

        problems = validate_fmu(args.fmu_filename)

        if len(problems) == 0:
            print('No problems found.')
        else:
            print('%d problems were found:' % len(problems))
            for message in problems:
                print()
                print(message)

        sys.exit(len(problems))

    elif args.command == 'compile':

        from fmpy.util import compile_platform_binary
        compile_platform_binary(args.fmu_filename, target_platform=args.target_platform)

    elif args.command == 'add-cswrapper':

        from fmpy.cswrapper import add_cswrapper
        add_cswrapper(args.fmu_filename)

    elif args.command == 'add-remoting':

        from fmpy.util import add_remoting
        from fmpy import supported_platforms

        platforms = supported_platforms(args.fmu_filename)

        if 'win32' in platforms and 'win64' not in platforms:
            add_remoting(args.fmu_filename, 'win64', 'win32')
        elif 'win64' in platforms and 'linux64' not in platforms:
            add_remoting(args.fmu_filename, 'linux64', 'win64')
        else:
            print("Failed to add remoting binaries.")

    elif args.command == 'create-cmake-project':

        import os
        from fmpy.util import create_cmake_project

        project_dir = args.cmake_project_dir

        if project_dir is None:
            project_dir = os.path.basename(args.fmu_filename)
            project_dir, _ = os.path.splitext(project_dir)
            print("Creating CMake project in %s" % os.path.abspath(project_dir))

        create_cmake_project(args.fmu_filename, project_dir)

    elif args.command == 'create-jupyter-notebook':

        from fmpy.util import create_jupyter_notebook

        create_jupyter_notebook(args.fmu_filename)

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

        if args.fmi_logging:
            fmi_call_logger = lambda s: print('[FMI] ' + s)
        else:
            fmi_call_logger = None

        result = simulate_fmu(args.fmu_filename,
                              validate=args.validate,
                              start_time=args.start_time,
                              stop_time=args.stop_time,
                              solver=args.solver,
                              step_size=args.step_size,
                              relative_tolerance=args.relative_tolerance,
                              output_interval=args.output_interval,
                              record_events=not args.dont_record_events,
                              fmi_type=None,
                              start_values=start_values,
                              apply_default_start_values=args.apply_default_start_values,
                              input=input,
                              output=args.output_variables,
                              timeout=args.timeout,
                              debug_logging=args.debug_logging,
                              visible=args.visible,
                              fmi_call_logger=fmi_call_logger)

        if args.output_file:
            write_csv(filename=args.output_file, result=result)

        if args.show_plot:
            plot_result(result=result, window_title=args.fmu_filename)
