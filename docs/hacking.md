# Hacking FMPy

You want to learn more about FMPy, debug it or contribute? Here's how to get started.

## Install uv

[Install uv](https://docs.astral.sh/uv/getting-started/installation/)

## Clone the repository

Go the directory where you want to clone the repository and enter

```
git clone https://github.com/CATIA-Systems/FMPy.git
```

or use your favorite Git tool to clone it. To check out the latest development branch change
to the directory and enter

## Get the native binaries

- create a virtual environment `uv venv fmpy-bootstrap`
- activate the environment `./fmpy-bootstrap/Scripts/activate`
- install the necessary packages `uv pip install fmpy requests toml`

**`Alternative 1:` download the native binaries from a previous release**

- download the binaries `python ./native/download_binaries.py`
- deactivate the virtual environment `deactivate`
- remove the virtual environment

**`Alternative 2:` compile the native binaries from source**

- change into the native directory `cd native`
- build CVode `python build_cvode.py`
- build the binaries `python build_binaries.py`
- build the remoting binaries (Windows and Linux only) `python build_remoting.py`

## Set up the virtual environment

`uv sync --all-extras`

## Start the GUI

`uv run python -m fmpy.gui`
