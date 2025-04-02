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

**`Alternative 1:` download the native binaries from a previous release**

This is the easiest way to get the native binaries if you don't want to compile them yourself.

- create a virtual environment `uv venv fmpy-bootstrap`
- activate the environment `./fmpy-bootstrap/Scripts/activate`
- install the necessary packages `uv pip install requests toml`
- download the binaries `python ./native/download_binaries.py`
- deactivate the virtual environment `deactivate`
- remove the virtual environment

**`Alternative 2:` compile the native binaries from source**

TODO
