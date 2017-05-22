.. image:: https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=master
    :target: https://travis-ci.org/CATIA-Systems/FMPy

FMPy
====

FMPy is a Python library to simulate `Functional Mockup Units (FMUs) <http://fmi-standard.org/>`_ that...

- supports FMI versions 1.0 and 2.0, Co-Simulation and Model Exchange
- runs on Windows and Linux
- validates the modelDescription.xml
- is pure Python (with ctypes)


Installation
------------

Install the latest release from PyPI

::

    $ sudo pip install fmpy

or install the latest development version from source

::

    $ git clone -b develop https://github.com/CATIA-Systems/FMPy.git
    $ cd fmpy
    $ sudo pip install .


Simulate an FMU from the command line
-------------------------------------

The following commands will download an FMU and simulate it using the settings
provided in the default experiment.

::

    $ wget https://trac.fmi-standard.org/browser/branches/public/Test_FMUs/FMI_2.0/CoSimulation/linux64#MapleSim/2016.2/CoupledClutches
    $ python -m fmpy.simulate CoupledClutches.fmu


Simulate an FMU in Python
-------------------------

For an example of how to simulate an FMU in Python see `coupled_clutches.py <fmpy/examples/coupled_clutches.py>`_.
To run the script type

::

    $ python -m fmpy.examples.coupled_clutches


------------------------------------

Copyright |copy| 2017 Dassault Systèmes

.. |copy|   unicode:: U+000A9
