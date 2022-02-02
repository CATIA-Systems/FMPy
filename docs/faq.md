## How do I update an existing installation of FMPy?

If you've installed FMPy with `conda`, open a conda prompt and run

```
conda update -c conda-forge fmpy
```

If you've installed FMPy with `pip`, run

```
pip install fmpy --upgrade
```

## How do I install a development build?

- go to the [CI server](https://dev.azure.com/CATIA-Systems/FMPy/)
- select `Pipelines > Pipelines`
- on the `Runs` page select the commit you want
- on the `Summary` tab click `N published` under `Related` (where `N` is the number of artifacts)
- hover over `merged`, click on `...` and select `Download artifacts`
- extract the downloaded ZIP archive
- open a command line and change into directory where you extracted the archive
- on the command line run `python -m pip install <path-to-wheel>` (where `<path-to-wheel>` is the path of the FMPy Wheel (*.whl))
