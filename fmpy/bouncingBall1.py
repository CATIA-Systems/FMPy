import matplotlib.pyplot as plt
from fmpy.simulate1 import simulate


#filename = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_1.0\CoSimulation\win64\Dymola\2017\Rectifier\Rectifier.fmu'
#filename = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_1.0\ModelExchange\win64\MapleSim\2016.2\ControlledTemperature\ControlledTemperature.fmu'
filename = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_1.0\ModelExchange\win64\Dymola\2017\DFFREG\DFFREG.fmu'

result = simulate(filename=filename, stop_time=25, step_size=0.1)

for name in ['dataOut1']:
    plt.plot(result['time'], result[name])

plt.show()
