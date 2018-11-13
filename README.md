[![Travis CI](https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=master)](https://travis-ci.org/CATIA-Systems/FMPy)
[![AppVeyor](https://ci.appveyor.com/api/projects/status/github/CATIA-Systems/FMPy?branch=master&svg=true)](https://ci.appveyor.com/project/TorstenSommer/fmpy)
[![PyPI version](https://badge.fury.io/py/fmpy.svg)](https://badge.fury.io/py/fmpy)
[![Anaconda-Server Badge](https://anaconda.org/conda-forge/fmpy/badges/version.svg)](https://anaconda.org/conda-forge/fmpy)
[![Documentation Status](https://readthedocs.org/projects/fmpy/badge/?version=latest)](http://fmpy.readthedocs.io/en/latest/?badge=latest)

# FMPy

FMPy is a free Python library to simulate [Functional Mock-up Units (FMUs)](http://fmi-standard.org/) that...

- supports FMI 1.0 and 2.0
- supports Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- has a graphical user interface
- compiles C code FMUs and generates CMake projects for debugging `NEW`

## Installation

Several options are available:

- Install with conda: `conda install -c conda-forge fmpy`
- Install with from PyPI: `python -m pip install fmpy[complete]`
- Install the latest development version directly from GitHub: `python -m pip install https://github.com/CATIA-Systems/FMPy/archive/develop.zip`

If you don't have Python on your machine you can install [Anaconda Python](https://www.anaconda.com/download/).

## Start the Graphical User Interface

You can start the FMPy GUI with `python -m fmpy.gui`

![FMPy GUI](docs/Rectifier_GUI.png)

## Simulate an FMU in Python

To follow this example download `Rectifier.fmu` for your platform by clicking on the respective link:
[Linux](https://github.com/modelica/fmi-cross-check/blob/master/fmus/2.0/cs/linux64/MapleSim/2017/Rectifier/Rectifier.fmu),
[macOS](https://github.com/modelica/fmi-cross-check/blob/master/fmus/2.0/cs/darwin64/MapleSim/2017/Rectifier/Rectifier.fmu),
[Windows (32-bit)](https://github.com/modelica/fmi-cross-check/blob/master/fmus/2.0/cs/win32/MapleSim/2017/Rectifier/Rectifier.fmu),
[Windows (64-bit)](https://github.com/modelica/fmi-cross-check/blob/master/fmus/2.0/cs/win64/MapleSim/2017/Rectifier/Rectifier.fmu).
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
  Generation Tool   MapleSim (1267140/1267140/1267140)
  Generation Date   2017-10-04T12:07:10Z

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

![Rectifier Result](docs/Rectifier_result.png)

## Simulate an FMU on the command line

To get information about an FMU directly from the command line change to the folder where you've saved the
FMU and enter

```
fmpy info Rectifier.fmu
```

Simulate the FMU and plot the results

```
fmpy simulate Rectifier.fmu --show-plot
```

Get more information about the available options

```
fmpy --help
```

## Advanced Usage

To learn more about how to use FMPy in you own scripts take a look at the
[coupled_clutches.py](fmpy/examples/coupled_clutches.py),
[custom_input.py](fmpy/examples/custom_input.py) and
[parameter_variation.py](fmpy/examples/parameter_variation.py) examples.

------------------------------------

&copy; 2018 Dassault Syst&egrave;mes
