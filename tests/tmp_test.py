from fmpy import simulate_fmu
from fmpy.util import download_file

print("----- TMP_TEST -----")
filename = download_file(
    'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/linux32/MapleSim/2015.2/Rectifier/Rectifier.fmu',
    checksum='7629fda38cd4078f9e7f512e9cbcf63a9ff67a58e7b2b56c972f4cd467fb85d6')

simulate_fmu(filename, fmi_type='CoSimulation', remote_platform='linux32')

print("----- END OF TMP_TEST -----")
