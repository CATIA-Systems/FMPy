FMPy
====

FMPy is a Python library to simulate Functional Mockup Units (FMUs).

- Supports FMI 2.0 Co-Simulation
- Windows 32 & 64 bit
- Validates the modelDescription.xml
- Pure Python (with ctypes)


Installation
------------

Clone the repository and change to the `FMPy` folder. On the command line type

```
python setup.py install
```


Tutorial
--------

The FMUs used in this tutorial can be downloaded from the [fmi-standard.org](https://trac.fmi-standard.org/browser/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/FMUSDK/2.0.3) website.

### Simulate an FMU

```
import matplotlib.pyplot as plt
from fmpy.simulate import simulate

result = simulate(filename=r'Z:\Development\FMPy\bouncingBall.fmu', start_values={'h': 1.5})

plt.plot(result['time'], result['h'])
plt.plot(result['time'], result['der(h)'])

plt.show()
```

### Set start values, stop time and step size

TODO...

### Set input





Copyright (c) 2015 3DS GmbH
