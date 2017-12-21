.. image:: https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=master
    :target: https://travis-ci.org/CATIA-Systems/FMPy

.. image:: https://ci.appveyor.com/api/projects/status/github/CATIA-Systems/FMPy?branch=master&svg=true

FMPy
====

FMPy is a free Python library to simulate `Functional Mock-up Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0
- supports Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- can validate FMUs
- provides fixed and variable-step solvers
- is pure Python (with ctypes)

Installation
------------

Get Python
^^^^^^^^^^

Download and install `Anaconda Python 3.6 <https://www.anaconda.com/download/>`_.
If you already have a Python installation you want to use you can skip this step.

Install FMPy
^^^^^^^^^^^^

To install FMPy using the conda package manager open a command line and enter::

    conda -c conda-forge fmpy

``Alternative 1:`` install from PyPI with::

    python -m pip install --upgrade fmpy

``Alternative 2:`` install the latest development version directly from GitHub::

    python -m pip install --upgrade https://github.com/CATIA-Systems/FMPy/archive/develop.zip

Simulate an FMU in Python
-------------------------

+---------------+----------+--------+---------------------+---------------------+
| Rectifier.fmu | `Linux`_ | macOS_ | `Windows (32-bit)`_ | `Windows (64-bit)`_ |
+---------------+----------+--------+---------------------+---------------------+

Download Rectifier.fmu for your platform, change to the folder where you've saved the FMU and open a Python prompt::

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

.. image:: Rectifier_result.png

Simulate an FMU on the command line
-----------------------------------

To get information about the FMU directly from the command line change to the folder where you downloaded the
FMU and enter::

    fmpy info Rectifier.fmu

Simulate the FMU and plot the results::

    fmpy simulate Rectifier.fmu --show-plot

To get more information about the available options::

    fmpy --help

Advanced Usage
--------------

To learn more about how to use FMPy in you own scripts take a look at the
`coupled_clutches.py <fmpy/examples/custom_input.py>`_,
`custom_input.py <fmpy/examples/custom_input.py>`_ and
`parameter_variation.py <fmpy/examples/custom_input.py>`_ examples.

------------------------------------

|copyright| 2017 |Dassault Systemes|

.. |copyright|   unicode:: U+000A9
.. |Dassault Systemes| unicode:: Dassault U+0020 Syst U+00E8 mes

.. _Linux: https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux64/MapleSim/2017/Rectifier/Rectifier.fmu
.. _macOS: https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/darwin64/MapleSim/2017/Rectifier/Rectifier.fmu
.. _Windows (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/MapleSim/2017/Rectifier/Rectifier.fmu
.. _Windows (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win64/MapleSim/2017/Rectifier/Rectifier.fmu
