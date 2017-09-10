.. image:: https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=master
    :target: https://travis-ci.org/CATIA-Systems/FMPy

.. image:: https://ci.appveyor.com/api/projects/status/github/CATIA-Systems/FMPy?branch=master&svg=true


FMPy
====

FMPy is a Python library to simulate `Functional Mockup Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI 1.0 and 2.0
- supports Co-Simulation and Model Exchange
- runs on Windows, Linux and macOS
- can validate FMUs
- is pure Python (with ctypes)


Installation
------------

To install the latest release from PyPI or update an existing installation type::

    python -m pip install --upgrade fmpy

or, to install the latest development version::

    python -m pip install --upgrade https://github.com/CATIA-Systems/FMPy/archive/develop.zip


Simulate an FMU on the command line
-----------------------------------

To simulate CoupledClutches.fmu and plot the results download the FMU for your platform
and run the following command in the folder where you downloaded the FMU::

    python -m fmpy.simulate CoupledClutches.fmu


+---------------------+---------------------+---------------------+-------------------+-------------------+--------+
| CoupledClutches.fmu | `Windows (32-bit)`_ | `Windows (64-bit)`_ | `Linux (32-bit)`_ | `Linux (64-bit)`_ | macOS_ |
+---------------------+---------------------+---------------------+-------------------+-------------------+--------+

.. _Windows (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Windows (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Linux (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux32/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _Linux (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu
.. _macOS: https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/darwin64/MapleSim/2016.2/CoupledClutches/CoupledClutches.fmu


Simulate an FMU in Python
-------------------------

For an example of how to simulate an FMU in Python see `coupled_clutches.py <fmpy/examples/coupled_clutches.py>`_.
To run the script type::

    python -m fmpy.examples.coupled_clutches


------------------------------------

|copyright| 2017 |Dassault Systemes|

.. |copyright|   unicode:: U+000A9
.. |Dassault Systemes| unicode:: Dassault U+0020 Syst U+00E8 mes
