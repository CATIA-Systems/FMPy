.. image:: https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=master
    :target: https://travis-ci.org/CATIA-Systems/FMPy

FMPy
====

FMPy is a Python library to simulate `Functional Mockup Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI versions 1.0 and 2.0
- supports FMI types Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- can validate FMUs
- is pure Python (with ctypes)


Installation
------------

To install the latest release from PyPI or update an existing installation type

::

    $ pip install fmpy --upgrade

on the command line or install the latest development version from source

::

    $ git clone -b develop https://github.com/CATIA-Systems/FMPy.git
    $ cd fmpy
    $ pip install .


Simulate an FMU from the command line
-------------------------------------

To simulate CoupledClutches.fmu and plot the results download the FMU for your platform
and run the following command in the folder where you downloaded the FMU.

::

    $ python -m fmpy.simulate CoupledClutches.fmu


+---------------------+---------------------+---------------------+-------------------+-------------------+----------+
| CoupledClutches.fmu | `Windows (32-bit)`_ | `Windows (64-bit)`_ | `Linux (32-bit)`_ | `Linux (64-bit)`_ | `macOS`_ |
+---------------------+---------------------+---------------------+-------------------+-------------------+----------+

.. _Windows (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Windows (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Linux (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux32/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Linux (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _macOS: https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/darwin64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu


Simulate an FMU in Python
-------------------------

For an example of how to simulate an FMU in Python see `coupled_clutches.py <fmpy/examples/coupled_clutches.py>`_.
To run the script type

::

    $ python -m fmpy.examples.coupled_clutches


------------------------------------

Copyright |copy| 2017 Dassault Systèmes

.. |copy|   unicode:: U+000A9
