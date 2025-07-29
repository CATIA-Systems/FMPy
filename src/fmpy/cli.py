""" Command line interface for FMPy """
from fmpy import extract


def main():

    import argparse
    import fmpy
    import sys
    import os

    description = f"""\
Validate and simulate Functional Mock-up Units (FMUs)

Get information about an FMU:
   
    fmpy info Rectifier.fmu
 
Simulate an FMU:
 
    fmpy simulate Rectifier.fmu --show-plot
    
Compile a source code FMU:

    fmpy compile Rectifier.fmu
    
Create a Jupyter Notebook

    fmpy create-jupyter-notebook Rectifier.fmu
    

About FMPy

FMPy version:       {fmpy.__version__}
FMI platform:       {fmpy.platform}
Installation path:  {os.path.dirname(__file__)}  
Python interpreter: {sys.executable}
Python version:     {sys.version}
"""

    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description=description)

    parser.add_argument('--version', action='version', version=f'FMPy version {fmpy.__version__}')

    parser.add_argument('command', choices=['info', 'validate', 'simulate', 'compile', 'remove-source-code',
                                            'add-cswrapper','add-remoting', 'create-cmake-project',
                                            'create-jupyter-notebook'],
                        help="Command to execute")
    parser.add_argument('fmu_filename', help="Filename of the FMU")

    simulate_group = parser.add_argument_group('simulate', "Simulate an FMU")
    simulate_group.add_argument('--show-plot', action='store_true', help="Plot the results")
    simulate_group.add_argument('--validate', action='store_true', help="Validate the FMU")
    simulate_group.add_argument('--start-time', type=float, help="Start time for the simulation")
    simulate_group.add_argument('--stop-time', type=float, help="Stop time for the simulation")
    simulate_group.add_argument('--solver', choices=['Euler', 'CVode'], default='CVode', help="Solver to use for Model Exchange")
    simulate_group.add_argument('--step-size', type=float, help="Step size for fixed-step solvers")
    simulate_group.add_argument('--relative-tolerance', type=float, help="Relative tolerance for the 'CVode' solver and FMI 2.0 co-simulation FMUs")
    simulate_group.add_argument('--dont-record-events', action='store_true', help="Dont't record outputs at events (model exchange only)")
    simulate_group.add_argument('--start-values', nargs='+', help="Name-value pairs of start values")
    simulate_group.add_argument('--apply-default-start-values', action='store_true', help="Apply the start values from the model description")
    simulate_group.add_argument('--output-interval', type=float, help="Interval for sampling the output")
    simulate_group.add_argument('--input-file', help="CSV file to use as input")
    simulate_group.add_argument('--output-variables', nargs='+', help="Variables to record")
    simulate_group.add_argument('--output-file', help="CSV to store the results")
    simulate_group.add_argument('--timeout', type=float, help="Max. time to wait for the simulation to finish")
    simulate_group.add_argument('--debug-logging', action='store_true', help="Enable the FMU's debug logging")
    simulate_group.add_argument('--visible', action='store_true', help="Enable interactive mode")
    simulate_group.add_argument('--fmi-logging', action='store_true', help="Enable FMI logging")
    simulate_group.add_argument('--cmake-project-dir', help="Directory for the CMake project")
    simulate_group.add_argument('--interface-type', help='Interface type ("ModelExchange" or "CoSimulation")')

    compile_group = parser.add_argument_group('compile', "Compile the platform binary")
    compile_group.add_argument('--generator', help="CMake generator")
    compile_group.add_argument('--platform', help="VisualStudio platform (ARM, Win32, x64)")
    compile_group.add_argument('--configuration', default="Release", help="Build configuration (Release or Debug)")
    compile_group.add_argument('--all-warnings', action='store_true', help="Enable all compiler warnings")
    compile_group.add_argument('--warning-as-error', action='store_true', help="Turn compiler warnings into errors")
    compile_group.add_argument('--cmake-options', nargs='+', help="CMake options")
    compile_group.add_argument('--with-wsl', action='store_true', help="Compile for Linux with WSL")

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

        from tempfile import TemporaryDirectory
        from fmpy.build import build_platform_binary
        from fmpy.util import create_zip_archive

        cmake_options = {
            "CMAKE_COMPILE_WARNING_AS_ERROR:BOOL": "ON" if args.warning_as_error else "OFF"
        }

        with TemporaryDirectory() as tempdir:
            extract(args.fmu_filename, unzipdir=tempdir)
            build_platform_binary(
                unzipdir=tempdir,
                generator=args.generator,
                platform=args.platform,
                configuration=args.configuration,
                all_warnings=args.all_warnings,
                with_wsl=args.with_wsl,
                cmake_options=cmake_options,
            )
            create_zip_archive(args.fmu_filename, tempdir)

    elif args.command == 'remove-source-code':

        from fmpy.util import remove_source_code
        remove_source_code(filename=args.fmu_filename)

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
                              fmi_type=args.interface_type,
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


if __name__ == '__main__':
    main()
