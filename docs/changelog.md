## v0.3.5 (2022-01-11)

### Bug fixes

- Convert return values of get*Status() functions to Python types (#352)
- Handle fmi2Discard returned by fmi2DoStep() (#353)
- Add fmi2SetDebugLogging() to client_sm.cpp (#355)
- Allow setting start values in Initialization Mode (#356)
- Suppress exceptions in GetLongPathName() (#217)

### Enhancements

- Update FMI headers to 3.0-beta.3
- Add parallelDoStep option to FMU Containter (#205)

## v0.3.4 (2021-12-10)

### Bug fixes

- Fix links to FMI Specs (#349)
- Fix validation of quoted variable names (#347)
- Set start values of Container FMU's variables (#345)

### Enhancements

- Use Dash 2.0 and update dependencies (#339)
- Raise FMICallExeption when FMI calls fail (#346)
- Add shared memory implementation for remoting on Windows (#328)
- Check if start values can be set (#351)

## v0.3.3 (2021-11-29)

### Bug fixes

- Add type cast to arguments of QMainWindows.resize() (#344)
- return filename in download_file() if file already exists (#332)
- Decode UTF-8 string in fmi3.printLogMessage()
- Handle c_bool in _log_fmi_args()
- Add default "initial" for fixed structural parameters (#340)
- Update time before recording result in custom input example (#333)
- Update icons for FMI 3 and add type column (#295)
- Change type hint for Unit.displayUnits to List[DisplayUnit] (#336)

### Enhancements

- Add Early Return and Event Mode for FMI 3.0 CS
- Calculate output_interval from fixedInternalStepSize
- Add type hint to FMU3Slave.doStep()
- Add unit and type definitions to Container FMU (#335)

## v0.3.2 (2021-10-14)

### Bug fixes

- Escape XML attributes in Container FMU (#216)
- Handle NULL pointers in fmi2Instantiate() in remoting client (#324)
- Add fmi2CancelStep() to remoting client (#325)
- Calculate t_next from n_fixed_steps (#318)
- Add trailing path separator to resourcePath in FMI 3.0 (#309)
- Don't plot multi-dimensional variables (#293)
- Fix type conversion in FMI 3.0 high level API (#300)
- Add attribute "interval" to ScalarVariable (#314)

### Enhancements

- Log FMI calls to nested FMUs if loggingOn == true
- Add Configuration class for FMU Container (#321)
- Use FMI import framework in FMU Container (#327)
- Use the Reference FMU's import framework in remoting server (#326)
- Check uniqueness of value references in FMI 3.0 (#294)
- Check for backslashes in ZIP file entries (#297)

## v0.3.1 (2021-07-21)

### Bug fixes

- Fix type hint for parameter "input" in "simulate_fmu()" (#286)
- Set output arguments in fmi3.intermediateUpdate() (#273)
- Allow fixed and tunable structural parameters (#268)
- Fix model structure of Container FMU (#267)
- Add missing parameter "nValues" to getString() and getBinary() and decode byte strings (#263)
- Set stop time and handle negative start time in (#261)

### Enhancements

- Update FMI 3.0 API to v3.0-beta.2
- Offer to open generated Jupyter notebook in GUI (#262)
- Add arguments of fmu_info() to dump() enhancement (#285)
- Improve Plotly plots of discrete signals (#284)
- Define variables of Container FMU independent of inner FMUs (#265)
- Validate that initial is not set for input and independent variables (#280)
- Return filename from fmpy.util.download_file() (#267)
- Add win64 on linux64 remoting w/ wine and linux64 on win64 remoting w/ WSL (experimental)
- Assert mandatory independent variable in FMI 3.0 (#272)
- Define model description classes with @attrs (#275)
- Detect drive letter in fmuResourceLocation on Windows

## v0.3.0 (2021-04-20)

This release drops Python 2.7 support. The minimum required version is now Python 3.5.

### Enhancements

- Update API to FMI 3.0-beta.1
- Add type hints to Model Description and simulate_fmu()
- Add "Hide All" and fix "Show All" columns in GUI
- Add target_platform parameter to compile_platform_binary()
- Link against libm when compiling platform binaries on Linux (#242)
- Add parameter set_input_derivatives to Input and simulate_fmu() (#240)
- Escape non-ASCII characters in XML attributes (#216)

## v0.2.27 (2021-01-28)

### Enhancements

- Scale icons on High DPI screens (#226)
- Add min and max columns and "Show All" action (#225)
- Update link to FMI 2.0.2 spec (#210)
- Handle missing documentation and model.png in web app (#187)
- Validate XML against schema in validate_fmu() (#223)
- Check for illegal start values (#224)
- Add "Validate FMU" action to GUI (#221)
- Set input derivatives for FMI 2.0 Co-Simulation (#214)
- Add "include" parameter to fmpy.extract() (#208)
- Handle missing "derivative" attribute in validate_fmu() (#206)
- Call SetProcessDpiAwareness(True) on Windows to avoid broken PyQtGraph plots (#201)

## v0.2.26 (2020-11-27)

### Enhancements

- Create "FMU Containers" with nested FMUs (experimental) (#193)
- Handle Scheduled Execution in instantiate_fmu() (#200)
- Add "create-jupyter-notebook" command to CLI (#192)
- Add all parameters to start_values in Jupyter Notebook (#190)
- Fix Boolean start values in Jupyter Notebooks (#188)
- Validate FMI 3 model description (#181)
- Remove assert statements from fmpy.sundials (#202)
- Update SSP schema to v1.0 and remove ssp.examples

## v0.2.25 (2020-11-04)

### Enhancements

- Add Dash based web app
- Add Jupyter Notebook generation
- Don't import NumPy in fmi1.py to allow reuse in projects with minimal dependencies (#184)
- Convert array indices in write_csv() to tuple to avoid FutureWarning

## v0.2.24 (2020-10-14)

### Enhancements

- Allow start values with units and display units
- Add FMI 3.0 Scheduled Execution API

## v0.2.23 (2020-09-02)

### Enhancements

- Add getAdjointDerivative() and fix getDirectionalDerivative()
- Validate results for FMI 3 Reference FMUs
- Add getClock() and setClock() to _FMU3
- Add FMU2Model.getNominalsOfContinuousStates()

### Bug fixes

- Fix logging for FMI 3 (#159)
- Read start value of String variables in FMI 3
- Add missing fields to EventInfoReturnValue message (#160)
- Move enterEventMode() and newDiscreteStates() to _FMU3
- Fix variabilities for variable type "Clock"

## v0.2.22 (2020-08-01)

- `FIXED' Forward fmi2NewDiscreteStates() in remoting client (#154)
- `FIXED` Fix createDesktopShortcut() and addFileAssociation() (#153)
- `NEW` Update FMI 3 API to 3.0-alpha.5

## v0.2.21 (2020-06-29)

- `FIXED` Set inputs in CVode root function before getting event indicators (#150)
- `FIXED` Add scipy to required packages for fmpy[plot] (#146)
- `FIXED` Activate conda environment in file open command and desktop shortcut (#131)
- `FIXED` Evaluate terminateSimulation in simulation loop (#145)
- `FIXED` Fix return value of FMU1Model.completedIntegratorStep()
- `FIXED` Add Dimension class and calculate initial shape of FMI 3 model variables
- `FIXED` Raise an exception when a missing FMI function is called (#139)
- `NEW` Update FMI 3 API to v3.0-alpha.4
- `NEW` Validate model structure in read_model_description()
- `NEW` Add "create-cmake-project" command to CLI (#129)
- `NEW` Add Co-Simulation wrapper and build binaries in CI (#127)

## v0.2.20 (2020-05-23)

- `FIXED` Fix fmi3Functions.h for compile_platform_binary()
- `FIXED` Fix serialization in write_csv() (#138)
- `FIXED` Check for existing documentation/licenses in add_remoting() (#126)
- `FIXED` Fix function names in RPC calls (#125)
- `CHANGED` Require pathlib only for Python version < 3.4
- `NEW` Update FMI 3 API to a51b173
- `NEW` Use defaultExperiment.tolerance as default in GUI (#133)
- `NEW` Add "Tools" menu to GUI (#124)
- `NEW` Make build configuration adjustable in build_remoting.py

## v0.2.19 (2020-04-15)

- `FIXED` fmi2SetupExperiment() is now called again in FMI 2.0 for Co-Simulation
- `FIXED` The working directory for the remoting server is now set to binaries/win32
- `FIXED` ssp.simulation.set_value() has been fixed for Integer and Enumeration variables
- `NEW` A license file is now added to documentation/licenses when adding the remoting binaries to an FMU
- `NEW` A stop_time parameter has been added to ssp.instantiate_fmu()
- `CHANGED` The license has been changed to 2-clause BSD

## v0.2.18 (2020-04-06)

- `FIXED` A list is now passed to np.stack() instead of an iterable and Iterable is now imported from collections.abc to avoid FutureWarnings.
- `FIXED` Argument checksum of function fmpy.util.download_file() can now be upper case.
- `FIXED` Start and stop time are now passed to initialize() in FMI 1.0.
- `FIXED` Variadic arguments in log messages are now processed.
- `NEW` The model.png is now displayed on the "Model Info" page of the GUI.
- `NEW` 32-bit FMUs can now be simulated in a 64-bit Python environment on Windows.
   Existing 32-bit FMUs can also be retro-fitted using the function fmpy.util.add_remoting(),
   the CLI (fmpy add-remoting ...) and the GUI (Help > Add 32-bit Remoting).
- `NEW` The FMI headers and schema have been updated to version 2.0.1 and 3.0-alpha.3 respectively.
- `NEW` The function instantiate_fmu() allows the instantiation and re-use of an FMU independent of the FMI version and type to reduce CPU time.
   See `examples/efficient_loops.py` for an example.
- `REMOVED` The parameter `use_source_code` has been removed form `simulate_fmu()` (use `fmpy.util.compile_platform_binary()` instead)

## v0.2.17 (2020-02-04)

- `NEW` "Clear Plots" action has been added to the context menu
- `IMPROVED` single quotes are now removed from name segments in the tree view
- `IMPROVED` a RuntimeError is raised when an errors occurs in CVode
- `IMPROVED` exceptions are raised for undefined declaredType, illegal combinations of causality and variability, and missing shared libraries
- `IMPROVED` communicationPoint is now calculated as n_steps * step_size to avoid accumulation of numerical errors

## v0.2.16 (2019-12-26)

- `FIXED` pre-compiled SUNDIALS libraries re-added

## v0.2.15 (2019-12-18)

- `FIXED` validation of structured variable names with apostrophes
- `FIXED` dimensions of variables in FMI 3
- `NEW` validation of "flat" variable names
- `UPDATED` FMI 3 schema files
- `UPDATED` CVode 5.0
- `IMPROVED` optional files added to CMake projects for source FMUs
- `IMPROVED` NULL pointers are now ignored in freeMemory()
- `IMPROVED` frequently used utility functions are now imported to fmpy module
- `IMPROVED` parameter_variation adapted to new Dask versions

## v0.2.14 (2019-10-23)

Improved validation & --visible option for CLI

- `FIXED` "Load Start Values" only enabled when FMU can be simulated
- `NEW` --visible option in CLI
- `NEW` XML line numbers added to validation messages
- `NEW` validation of variables names for naming convention "structured"
- `IMPROVED` visible=fmi2True when simulating in GUI

## v0.2.13 (2019-09-16)

Extended FMI 3.0 alpha 2 support & improved GUI

- `NEW` check for illegal filenames in FMU archives
- `NEW` reload button in GUI
- `IMPROVED` extended FMI 3.0 alpha 2 support
- `CHANGED` increased max. filesize for Cross-Check FMUs

## v0.2.12 (2019-07-15)

Support for FMI 3.0 Alpha 1, output interval in GUI

- `FIXED` compilation of platform binary on Windows 32-bit
- `IMPROVED` support for FMI 3.0 Alpha 1
- `IMPROVED` output interval can now be set in the GUI
- `IMPROVED` output interval is now calculated based on stepSize attribute

## v0.2.11 (2019-05-27)

FMPy 0.2.11: improved robustness and validation

- `FIXED` leading spaces in dependency list are now handled correctly
- `FIXED` input files with only one sample can now be handled
- `IMPROVED` errors during cleanup of temporary directories are now ignored
- `IMPROVED` "Relative Tolerance" input field is now enabled for Co-Simulation FMUs
- `IMPROVED` compilation of source code FMUs is now more robust
- `IMPROVED` combinations of causality and variability are now validated
- `IMPROVED` assertions for required start values have been added
- `IMPROVED` assertions for unique variable names have been added

## v0.2.10 (2019-02-26)

Experimental FMI 3.0 support, FMI Cross-Check validation scripts

- `FIXED` set start values before entering initialization mode
- `NEW` experimental FMI 3.0 support
- `NEW` FMI Cross-Check validation scripts to validate FMUs and results
- `IMPROVED` handling of reference signals with duplicate sample times

## v0.2.9 (2019-02-07)

Improved logging, discrete inputs and tunable parameters

- `FIXED` handling of discrete inputs
- `FIXED` set continuous states after solver step
- `NEW` set tunable parameters via input
- `IMPROVED` disable inactive root warnings for CVode
- `IMPROVED` error and log messages
- `IMPROVED` plotting of discrete signals

## v0.2.8 (2018-12-24)

- `FIXED` Handle optional elements in ScalarVariable tag
- `FIXED` Handle null pointers in FMI logging
- `FIXED` Relax type of attribute "version" in fmiModelDescription.xsd to "normalizedString"
- `FIXED` Fix size of memory passed to fmi2DeSerializeFMUstate()
- `NEW` Validate modelDescription.outputs
- `NEW` Add compilation with Visual Studio 2017
- `NEW` Add missing attributes to ScalarVariable and validate derivatives and units
- `NEW` Change input extrapolation to "hold"

## v0.2.7 (2018-11-13)

- `FIXED` Test files are now downloaded form GitHub
- `FIXED` Compilation of model exchange FMUs works now
- `NEW` --relative-tolerance parameter is now passed to FMI 2.0 co-simulation FMUs
- `NEW` Platform binary can now be compiled from within the GUI (Help > Compile Platform Binary)

## v0.2.6 (2018-09-04)

- `NEW` CMake project generation for C code FMUs
- `NEW` Read Enumeration items from modelDescription.xml
- `FIXED` GUI with Python 2.7

## v0.2.5 (2018-06-17)

Improved handling of input signals

- input is now applied before initialization for co-simulation
- "time" column for input signals can now have an arbitrary name


## v0.2.4 (2018-05-22)

- `NEW` Remaining FMI functions added
- `NEW` More options for command line interface
- `NEW` More elements added to SSP parser
- `NEW` Polished GUI
- `FIXED` No more warning when starting GUI


## v0.2.3 (2018-04-11)

- `NEW` Allow simulation of extracted FMUs and pre-loaded model descriptions
- `NEW` Re-load an FMU in the GUI
- `NEW` Load start values from an FMU
- `NEW` Write changed start values back to the FMU
- `NEW` Table editor for 1-d and 2-d array variables
- `NEW` Handle events in input signals
- `NEW` Plot events
- `NEW` Regular time grid for model-exchange results
- `NEW` Apply start values in the model description
- `NEW` Debug and FMI logging on the command line and in the GUI
- `NEW` Log filtering by type and message in the GUI
- `FIXED` Logger callback for FMI 1.0
- `FIXED` Handling of `None` in setString()
- `FIXED` Handling of time events
- `FIXED` Conversion of Boolean start values


## v0.2.2 (2018-03-13)

- `NEW` FMI 2.0 state serialization functions added
- `NEW` Graphical representation of the FMU's inputs and outputs added to settings page
- `NEW` Platform check when simulating FMUs
- `NEW` MkDocs documentation added
- `FIXED` Record values at time == start_time when simulating model exchange FMUs
- `FIXED` Correct source files are now used when compiling model exchange FMUs
- `CHANGED` Required dependency on pypiwin32 changed to pywin32


## v0.2.1 (2018-02-15)

- `NEW` About dialog in the GUI that shows version and environment info
- `NEW` Copy variable names and value references to the clipboard from the context menu
- `NEW` Navigation buttons are new toggled to indicated selected page
- `FIXED` fmu_info() now works with FMUs where not all attributes are set in the modelDescription.xml
- `FIXED` Improved error message when the FMU does not support the selected FMI type


## v0.2.0 (2018-01-29)

- `NEW` graphical user interface
- `NEW` compilation of source code FMUs
- `NEW` model structure elements: ModelDescription.outputs and ModelDescription.derivatives
- `NEW` FMI functions: setRealInputDerivatives() and getRealOutputDerivatives()
- `FIXED` constructor arguments for solver classes


## v0.1.2 (2017-12-21)

- `CHANGED` 'fmpy' command is now directly accessible from the command line
- `CHANGED` SSP schema updated to Draft20171219


## v0.1.1 (2017-12-11)

- `NEW` dependency information in setup.py
- `NEW` platform check for parameter variation example
- `FIXED` FMI call logging
- `FIXED` plot_result() now works with older matplotlib versions
- `CHANGED` timeout in cross-check removed


## v0.1.0 (2017-11-24)

- `NEW` custom simulation loop and input example
- `NEW` parameter variation example running on multiple cores
- `NEW` experimental [System Structure and Parameterization](https://www.modelica.org/projects#ssp) support
- `NEW` max. step size parameter for CVode solver
- `FIXED` return values in completedIntegratorStep()


## v0.0.9 (2017-10-13)

- `FIXED` set start values of type String
- `NEW` CVode variable-step solver
- `NEW` cross-check API for external tools


## v0.0.8 (2017-09-10)

- `FIXED` resourceLocation in FMU2.instantiate() now points to resources directory instead of unzip directory
- `NEW` FMI functions (fmi1Reset, fmi2Reset, fmi2GetFMUState, fmi2SetFMUState, fmi2FreeFMUState)
