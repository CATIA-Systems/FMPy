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

To install the latest release from PyPI or update an existing installation type::

    python -m pip install --upgrade fmpy

or, to install the latest development version::

    python -m pip install --upgrade https://github.com/CATIA-Systems/FMPy/archive/develop.zip


Simulate an FMU on the command line
-----------------------------------

To simulate Rectifier.fmu and plot the results download the FMU for your platform
and run the following command in the folder where you downloaded the FMU::

    python -m fmpy.simulate Rectifier.fmu --show-plot


+---------------+---------------------+---------------------+-------------------+-------------------+--------+
| Rectifier.fmu | `Windows (32-bit)`_ | `Windows (64-bit)`_ | `Linux (32-bit)`_ | `Linux (64-bit)`_ | macOS_ |
+---------------+---------------------+---------------------+-------------------+-------------------+--------+

.. _Windows (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/MapleSim/2016.2/Rectifier/Rectifier.fmu
.. _Windows (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win64/MapleSim/2016.2/Rectifier/Rectifier.fmu
.. _Linux (32-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux32/MapleSim/2016.2/Rectifier/Rectifier.fmu
.. _Linux (64-bit): https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux64/MapleSim/2016.2/Rectifier/Rectifier.fmu
.. _macOS: https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/darwin64/MapleSim/2016.2/Rectifier/Rectifier.fmu

.. image:: Rectifier_result.png

To get more information about the available options type::

    python -m fmpy.simulate --help


Simulate an FMU in Python
-------------------------

For an example of how to simulate an FMU in Python see `coupled_clutches.py <fmpy/examples/coupled_clutches.py>`_.
To run the script type::

    python -m fmpy.examples.coupled_clutches


Connect an FMU to custom input
------------------------------

The `custom_input.py <fmpy/examples/custom_input.py>`_ example shows how to use the FMU class directly to build a custom
simulation loop and how to get and set model variables to control the simulation.


------------------------------------

|copyright| 2017 |Dassault Systemes|

.. |copyright|   unicode:: U+000A9
.. |Dassault Systemes| unicode:: Dassault U+0020 Syst U+00E8 mes
