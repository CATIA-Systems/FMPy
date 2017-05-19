[![Build Status](https://travis-ci.org/CATIA-Systems/FMPy.svg?branch=feature/travis-ci)](https://travis-ci.org/CATIA-Systems/FMPy)

FMPy
====

FMPy is a Python library to simulate Functional Mockup Units (FMUs) that

- supports FMI 2.0 Co-Simulation
- runs on Windows and Linux (32 & 64 bit)
- validates the modelDescription.xml
- is pure Python (with ctypes)


Installation
------------

```
pip install fmpy-<version>.zip
```


Tutorial
--------

The FMU used in this tutorial can be downloaded from the [fmi-standard.org](https://trac.fmi-standard.org/browser/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/FMUSDK/2.0.3) website.

### Simulate an FMU

```
import matplotlib.pyplot as plt
from fmpy.simulate import simulate

result = simulate(filename='bouncingBall.fmu', start_values={'h': 1.5})

plt.plot(result['time'], result['h'])
plt.plot(result['time'], result['der(h)'])

plt.show()
```


Copyright (c) 2017 Dassault Sytemes
