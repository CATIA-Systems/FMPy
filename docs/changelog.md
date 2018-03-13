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
