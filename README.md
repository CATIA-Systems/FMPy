FMPy
====

FMPy is a Python library to simulate Functional Mockup Units (FMUs).

Example
-------

The `bouncingBall.fmu` is available from [fmi-standard.org](https://trac.fmi-standard.org/browser/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win32/FMUSDK/2.0.3/BouncingBall).

```
import matplotlib.pyplot as plt
from fmpy.simulate import simulate

result = simulate(filename=r'Z:\Development\FMPy\bouncingBall.fmu', start_values={'h': 1.5})

plt.plot(result['time'], result['h'])
plt.plot(result['time'], result['der(h)'])

plt.show()
```

Getting Startet
---------------

Clone the repository and change to the `FMPy` folder. On the command line type

```
python setup.py install
```

Copyright (c) 2015 3DS GmbH
