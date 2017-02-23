import matplotlib.pyplot as plt
from fmpy.simulate1 import simulate


filename = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_1.0\CoSimulation\win64\Dymola\2017\Rectifier\Rectifier.fmu'

result = simulate(filename=filename, stop_time=0.1, step_size=1e-4)

for name in ['Losses']:
    plt.plot(result['time'], result[name])

plt.show()
