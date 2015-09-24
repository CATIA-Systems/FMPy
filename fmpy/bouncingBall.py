import numpy as np
from fmpy import *


fmu = FMU2(unzipdir=r'Z:\Development\FMPy\bouncingBall')

time = 0.0
stop = 3.0
step = 1e-2

names = ['h', 'der(h)']
result = []

fmu.instantiate('bouncingBall', fmi2CoSimulation)
fmu.setupExperiment(tolerance=None, startTime=time)
fmu.enterInitializationMode()
fmu.exitInitializationMode()

vr = (fmi2ValueReference * len(names))()

for i, name in enumerate(names):
    vr[i] = fmu.variables[name].valueReference

result = []

while time < stop:
    status = fmu.doStep(time, step, fmi2True)
    result.append([time] + fmu.getReal(vr))
    time += step

fmu.terminate()
fmu.freeInstance()

import matplotlib.pyplot as plt

res = np.array(result)

plt.plot(res[:,0], res[:,1])
plt.plot(res[:,0], res[:,2])
plt.show()

pass