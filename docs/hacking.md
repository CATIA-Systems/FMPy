# Hacking FMPy

You want to learn more about FMPy, debug it or contribute? Here's how to get started.

## Setup your Python environment

**`Alternative 1:` Create a a new Conda environment (recommended)**

If you don't have conda yet you can either install [Anaconda](https://www.anaconda.com/download/) which includes
the most common Python packages or [Miniconda](https://conda.io/miniconda.html) which only contains the conda package manager
and Python.

To create a new conda environment named "py36_64" enter

```bash
conda create -q -n py36_64 -c anaconda python=3.6 dask lxml matplotlib numpy pyqt pyqtgraph pywin32 requests
```

on Linux and macOS the `pywin32` package is not required but you might need to prepend `sudo` to
the command depending on your permissions.
If you want a 32-bit Python environment you have to enter `set CONDA_FORCE_32BIT=1` before creating
the environment. Note that in order to simulate FMUs the Python environment has to match the
platforms supported by the FMU. I.e. you need a 64-bit Python on Windows to simulate an FMU that
only supports `win64`. To activate the environment run `activate py36_64` on Windows or `source activate py36_64` on Linux and macOS and `deactivate` to deactivate it.

**`Alternative 2:` Use an existing Python environment**

If you want to use an existing Python you can install the necessary dependencies with conda

```bash
conda install dask lxml matplotlib numpy pyqt pyqtgraph pywin32 requests
```

or pip

```bash
python -m pip install dask lxml matplotlib numpy pyqt pyqtgraph pywin32 requests
```

The package `pywin32` is only required on Windows.


## Clone the repository

Go the directory where you want to clone the repository and enter

```bash
git clone https://github.com/CATIA-Systems/FMPy.git
```

or use your favorite Git tool to clone it. To checkout the latest development branch change
to the directory and enter

```bash
git fetch
git checkout -b develop origin/develop
```

## Install FMPy

To install or update FMPy without changing the dependencies of your python environment change to the folder where you cloned FMPy and run

```bash
python -m pip install --upgrade --no-deps .
```

To use the sources directly, install FMPy in [develop mode](https://pip.pypa.io/en/stable/reference/pip_install/#cmdoption-e) using the `--editable` option

```bash
python -m pip install --no-deps --editable .
```

## Create a PyCharm project

Download and install [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/). On the welcome screen click `Create New Project` or select `File > New Project...`.

As `Location` select the `FMPy` directory you just cloned. Expand `Project Interpreter`, check `Existing Interpreter` and select
the environment you created. You might need to add your interpreter first using the cogwheel button. After clicking `Create` a dialog pops up asking if you want to create a project from existing sources. Click `Yes`.

## Debug the "coupled_clutches" example

Open `FMPy > fmpy > examples > coupled_clutches.py` from the project view and put a breakpoint in `def simulate_coupled_clutches()` by left-clicking between the line number and the code. To start debugging right-click on `coupled_clutches.py` and select `Debug 'coupled_clutches'`.
Use the buttons in the debug view to step through the code.

## Debug the GUI

Click on the drop-down box on the top-right and select `Edit Configurations...`. In the dialog click on the `+` button and select `Python` to add a new run configuration. Fill in the following values:

Option               | Value
---------------------|----------
Name                | FMPy GUI
Script path         | fmpy.gui
Python interpreter  | the environment you've created
Interpreter options | -m

Now you can set breakpoints and start debugging by clicking on the debug button on the top right.
