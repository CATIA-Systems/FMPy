import fmpy
import requests
import unittest


class TestFMUInfo(unittest.TestCase):

    def test_fmu_info(self):

        url = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/FMI_2.0/CoSimulation/win64/FMUSDK/2.0.4/BouncingBall/bouncingBall.fmu'

        print('Downloading FMU...')

        response = requests.get(url)

        with open('bouncingBall.fmu', 'wb') as f:
            f.write(response.content)

        print('done.')

        version, interfaces = fmpy.fmu_info('bouncingBall.fmu')

        self.assertEqual(version, '2.0')


if __name__ == '__main__':
    unittest.main()
