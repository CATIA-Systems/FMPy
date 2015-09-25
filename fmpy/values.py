import matplotlib.pyplot as plt
from fmpy.simulate import simulate


result = simulate(filename='values.fmu', stop_time=10, step_size=0.1)

names = result.dtype.names

for i, name in enumerate(names):
    plt.subplot(len(names), 1, i+1)
    plt.plot(result['time'], result[name])
    plt.ylabel(name)

plt.show()
