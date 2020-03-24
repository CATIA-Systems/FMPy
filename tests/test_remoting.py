import unittest
from unittest import skipIf
from fmpy import platform, supported_platforms, simulate_fmu
from fmpy.util import add_remoting, download_file


@skipIf(platform != 'win64', "Remoting is only supported on Windows 64-bit")
class RemotingTest(unittest.TestCase):

    def test_remoting_cs(self):

        download_file('https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win32/FMUSDK/2.0.4/vanDerPol/vanDerPol.fmu')

        filename = 'vanDerPol.fmu'

        self.assertNotIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='CoSimulation')

        add_remoting(filename)

        self.assertIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='CoSimulation')

    def test_remoting_me(self):

        download_file('https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win32/FMUSDK/2.0.4/vanDerPol/vanDerPol.fmu')

        filename = 'vanDerPol.fmu'

        self.assertNotIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='ModelExchange')

        add_remoting(filename)

        self.assertIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='ModelExchange')
