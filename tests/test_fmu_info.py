import fmpy
import requests
import unittest


class TestFMUInfo(unittest.TestCase):

    def test_fmu_info(self):

        print(fmpy.__file__)

        test_fmus_repository = 'https://trac.fmi-standard.org/export/HEAD/branches/public/Test_FMUs/'

        fmu = 'CoupledClutches.fmu'

        url = test_fmus_repository + 'FMI_2.0/CoSimulation/' + fmpy.platform + '/MapleSim/2016.2/CoupledClutches/' + fmu

        print('Downloading ' + fmu)

        response = requests.get(url)

        with open(fmu, 'wb') as f:
            f.write(response.content)

        # get fmu info
        version, interfaces = fmpy.fmu_info(fmu)

        self.assertEqual(version, '2.0')

        print('Simulating ' + fmu)

        res = fmpy.simulate(fmu)

        print('Result length: %d' % res['time'].size)
        print('Result signals: ' + ', '.join(res.dtype.names))


if __name__ == '__main__':

    unittest.main()
