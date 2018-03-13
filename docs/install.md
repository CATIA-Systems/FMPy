## Get Python

To use FMPy you need Python. If you do not have a Python environment on your machine you can install
[Anaconda](https://www.anaconda.com/download/) that comes with a range of packages for scientific computing. If you want
to install your packages individually you can use [Miniconda](https://conda.io/miniconda.html).

## Required Packages

Depending on what you intent to use FMPy for you might only need certain packages.

| Function                  | Required packages                         |
|---------------------------|-------------------------------------------|
| Read modelDescription.xml | lxml                                      |
| Simulate FMUs             | numpy, pathlib, pywin32 (only on Windows) |
| Plot results              | matplotlib                                |
| Parallelization example   | dask                                      |
| Download example FMUs     | requests                                  |
| Graphical user interface  | pyqt, pyqtgraph                           |


## Install with Conda

To install FMPy from [conda-forge](https://conda-forge.org/) including all dependencies type

```bash
conda install -c conda-forge fmpy
```

To install FMPy w/o dependencies type

```bash
conda install -c conda-forge fmpy --no-deps
```

and install the dependencies with

```bash
conda install <packages>
```


## Install with PIP

To install FMPy from [PyPI](https://pypi.python.org/pypi) including all dependencies type

```bash
python -m pip install fmpy[complete]
```

To install FMPy w/o dependencies type

```bash
python -m pip install fmpy --no-deps
```

and install the dependencies with

```bash
python -m pip install <packages>
```


## Install from Source

To install the latest development version directly from GitHub type

```bash
python -m pip install https://github.com/CATIA-Systems/FMPy/archive/develop.zip
```
