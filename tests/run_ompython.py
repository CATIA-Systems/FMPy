import os

import OMPython
from OMPython import OMCSessionZMQ

os.environ['OPENMODELICAHOME'] = r'E:\OpenModelica'

omc = OMCSessionZMQ()

commands = [
    'loadFile("E:/Development/FMPy/fmpy/modelica/FMI/package.mo")',
    'loadFile("E:/Development/FMPy/tests/resources/FMITest/package.mo")',
    'simulate(FMITest.BouncingBall_CS, stopTime=4)',
]

for command in commands:
    print(command)
    result = omc.sendExpression(command)
    print(result)

print('done')
