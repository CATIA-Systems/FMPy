import matplotlib.pyplot as plt
from fmpy.simulate import simulate


result = simulate(filename=r'Z:\Development\FMPy\bouncingBall.fmu', start_values={'h': 1.5})

plt.plot(result['time'], result['h'])
plt.plot(result['time'], result['der(h)'])

plt.show()