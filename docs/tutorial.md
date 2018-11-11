## Graphical User Interface

You can start the FMPy GUI with `python -m fmpy.gui`

![FMPy GUI](Rectifier_GUI.png)

## Python

To follow this example download `Rectifier.fmu` for your platform by clicking on the respective link:
[Linux](https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/linux64/MapleSim/2018/Rectifier/Rectifier.fmu),
[macOS](https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/darwin64/MapleSim/2018/Rectifier/Rectifier.fmu),
[Windows (32-bit)](https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win32/MapleSim/2018/Rectifier/Rectifier.fmu),
[Windows (64-bit)](https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win64/MapleSim/2018/Rectifier/Rectifier.fmu).
Change to the folder where you've saved the FMU and open a Python prompt.

```
>>> from fmpy import *
>>> fmu = 'Rectifier.fmu'
>>> dump(fmu)  # get information

Model Info

  FMI Version       2.0
  Model Name        Rectifier
  Description       Model Rectifier
  Platforms         win64
  Continuous States 4
  Event Indicators  6
  Variables         63
  Generation Tool   MapleSim (1357016/1357197/1357197)
  Generation Date   2018-10-25T13:27:33Z

Default Experiment

  Stop Time         0.1
  Step Size         1e-07

Variables (input, output)

Name                Causality          Start Value  Unit     Description
outputs             output        282.842712474619  V        Rectifier1.Capacitor1.v
>>> result = simulate_fmu(fmu)         # simulate the FMU
>>> from fmpy.util import plot_result  # import the plot function
>>> plot_result(result)                # plot two variables
```

![Rectifier Result](Rectifier_result.png)

## Command Line Interface

To get information about an FMU directly from the command line change to the folder where you've saved the
FMU and enter

```bash
fmpy info Rectifier.fmu
```

Simulate the FMU and plot the results

```bash
fmpy simulate Rectifier.fmu --show-plot
```

Get more information about the available options

```bash
fmpy --help
```

## Advanced Usage

To learn more about how to use FMPy in you own scripts take a look at the
[coupled_clutches.py](https://github.com/CATIA-Systems/FMPy/blob/master/fmpy/examples/coupled_clutches.py),
[custom_input.py](https://github.com/CATIA-Systems/FMPy/blob/master/fmpy/examples/custom_input.py) and
[parameter_variation.py](https://github.com/CATIA-Systems/FMPy/blob/master/fmpy/examples/parameter_variation.py) examples.

## Debugging C code FMUs

FMPy can generate [CMake](https://cmake.org/) projects for C code FMUs that allow you to conveniently build and debug FMUs in your favorite IDE. To debug an FMU using Visual Studio Solution follow these steps:

- Open the FMU in the FMPy GUI, click `Help > Create CMake Project...` and select the directory to save the project files

- Open the CMake GUI and select the source and build directories (you can set both to the above directory)

- Click `Configure` and select the generator (e.g. `Visual Studio 14 2015 Win64` to create a Visual Studio 2015 solution for 64-bit Windows)

- Click `Generate` to create the Visual Studio solution

- Click `Open Project` to open the solution

- In Visual Studio select `Build > Build Solution` to build the debug FMU

- Open the FMU that has been created in the project directory in the FMPy GUI

- In Visual Studio select `Debug > Attach to Process...`, select the Python process that runs the FMPy GUI and click `Attach`

- Set a breakpoint

- Run the simulation in the FMPy GUI and start debugging
