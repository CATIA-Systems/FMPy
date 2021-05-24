import shutil
import unittest
from unittest import skipIf
from fmpy import platform, supported_platforms, simulate_fmu, extract
from fmpy.util import add_remoting, download_file, has_wsl, has_wine64


class RemotingTest(unittest.TestCase):

    @skipIf(platform != 'win64', "Windows 32-bit is only supported on Windows 64-bit")
    def test_remoting_win32_on_win64_cs(self):

        download_file(
            'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win32/FMUSDK/2.0.4/vanDerPol/vanDerPol.fmu',
            checksum='6a782ae3b3298081f9c620a17dedd54370622bd2bb78f42cb027243323a1b805')

        filename = 'vanDerPol.fmu'

        self.assertNotIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='CoSimulation', remote_platform='win32')

        add_remoting(filename, 'win64', 'win32')

        self.assertIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='CoSimulation', remote_platform=None)

    @skipIf(platform != 'win64', "Windows 32-bit is only supported on Windows 64-bit")
    def test_remoting_win32_on_win64_me(self):

        download_file(
            'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/me/win32/FMUSDK/2.0.4/vanDerPol/vanDerPol.fmu',
            checksum="1c2e40322586360d58fcffa8eb030dd9edb686ef7a0f2bad1e9d59d48504d56a")

        filename = 'vanDerPol.fmu'

        self.assertNotIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='ModelExchange', remote_platform='win32')

        add_remoting(filename, 'win64', 'win32')

        self.assertIn('win64', supported_platforms(filename))

        simulate_fmu(filename, fmi_type='ModelExchange', remote_platform=None)

    @skipIf(not has_wsl(), "Requires Windows 64-bit and WSL")
    def test_remoting_linux64_on_win64(self):

        download_file(
            'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/linux64/MapleSim/2021.1/Rectifier/Rectifier.fmu',
            checksum='b9238cd6bb684f1cf5b240ca140ed5b3f75719cacf81df5ff0cae74c2e31e52e')

        filename = 'Rectifier.fmu'

        self.assertNotIn('win64', supported_platforms(filename))

        simulate_fmu(filename, remote_platform='linux64')

    @skipIf(not has_wine64(), "Requires Linux 64-bit and wine 64-bit")
    def test_remoting_win64_on_linux64_cs(self):

        download_file(
            'https://github.com/modelica/fmi-cross-check/raw/master/fmus/2.0/cs/win64/Dymola/2019FD01/DFFREG/DFFREG.fmu',
            checksum='b4baf75e189fc7078b76c3d9f23f6476ec103d93f60168df4e82fa4dc053a93c')

        filename = 'DFFREG.fmu'

        self.assertNotIn('linux64', supported_platforms(filename))

        simulate_fmu(filename, remote_platform='win64')

        add_remoting(filename, 'linux64', 'win64')

        self.assertIn('win64', supported_platforms(filename))

        simulate_fmu(filename, remote_platform=None)
