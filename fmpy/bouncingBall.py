
from ctypes import *
from itertools import combinations

import numpy as np
from fmpy import *


fmu = FMU2()

fmu.instantiate('bouncingBall', fmi2CoSimulation)

fmu.setupExperiment(False, 0.0, 0.0, True, 3.0)

fmu.enterInitializationMode()
fmu.exitInitializationMode()

step = 1e-2

time = np.linspace(0, 2.5, 251)

vr    = (fmi2ValueReference * 1)(0)
value = (fmi2Real * 1)(0.0)


height = [0.0]

for t, h in zip(time[1:], np.diff(time)):
    status = fmu.doStep(t, h, fmi2True)
    status = fmu.getBooleanStatus(fmi2Terminated)
    value = fmu.getReal(vr)

    print "%g, %g" % (t, value[0])
    t += step

    height.append(value[0])

fmu.terminate()
fmu.freeInstance()

import matplotlib.pyplot as plt

plt.plot(time, height)
plt.show()

pass