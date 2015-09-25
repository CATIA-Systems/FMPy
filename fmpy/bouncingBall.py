import matplotlib.pyplot as plt
from fmpy.simulate import simulate


result = simulate(filename='bouncingBall.fmu', start_values={'h': 1.5}, stop_time=2.5)

for name in ['h', 'der(h)']:
    plt.plot(result['time'], result[name])

plt.show()
