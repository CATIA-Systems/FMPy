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
