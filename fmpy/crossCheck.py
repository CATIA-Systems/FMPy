import os
import numpy as np
import matplotlib.pyplot as plt
from collections import Iterable
from fmpy.simulate import simulate
from unittest import TestCase
import fmpy
from scipy.interpolate import interp1d

def simulateFMU(path: str, reportDir=None):

    input_filename = None

    for file in os.listdir(path):

        if file.endswith('.fmu'):
            fmu_filename = file

        if file.endswith('_in.csv'):
            input_filename = file

        if file.endswith('_ref.csv'):
            reference_filename = file

        if file.endswith('_cc.bat'):
            batch_filename = file

    print(path, fmu_filename)

    ref = np.genfromtxt(os.path.join(path, reference_filename), delimiter=',', names=True)

    if input_filename is not None:
        input = np.genfromtxt(os.path.join(path, input_filename), delimiter=',', names=True)
    else:
        input = None

    time = ref['time']

    sample_interval = time[1] - time[0]
    stop_time = time[-1]

    step_size = stop_time / 1000

    if batch_filename is not None:

        with open(os.path.join(path, batch_filename), 'r') as file:
            for line in file:
                args = line.split(' ')
                if '-h' in args:
                    i = args.index('-h')
                    step_size = float(args[i+1])
                    break

    res = simulate(filename=os.path.join(path, fmu_filename),
                   stop_time=stop_time,
                   step_size=step_size,
                   output=ref.dtype.names[1:],
                   sample_interval=sample_interval,
                   input=input)

    names = res.dtype.names[1:]

    outliers = 0

    for name in names:
        t_ref = ref['time']
        y_ref = ref[name]

        t_res = res['time']
        y_res = res[name]

        lower, upper = get_limits(y_ref)

        f_u = interp1d(t_ref, upper, fill_value='extrapolate')
        f_l = interp1d(t_ref, lower, fill_value='extrapolate')

        outside = np.logical_or(y_res < f_l(t_res), y_res > f_u(t_res))

        outliers += np.sum(outside)

    # if outliers > 0:
    #     plot_result(res, ref)

    if reportDir is not None:
        header = ','.join(map(lambda s: '"' + s + '"', res.dtype.names))
        np.savetxt(os.path.join(reportDir, 'result.csv'), res, delimiter=',', header=header, comments='', fmt='%g')
        plot_result(res, ref, filename=os.path.join(reportDir, 'result.png'))

    return outliers


def get_limits(y_ref, margin=0.02):

    dy = np.abs(y_ref).max() * margin

    _, S = np.meshgrid(range(5), y_ref, indexing='ij')

    # S[0, :-3] = y_ref[3:]
    S[0, :-2] = y_ref[2:]
    S[1, :-1] = y_ref[1:]
    S[2, :]   = y_ref
    S[3, 1:]  = y_ref[:-1]
    S[4, 2:]  = y_ref[:-2]
    # S[6, 3:]  = y_ref[:-3]

    lower = np.min(S, axis=0) - dy
    upper = np.max(S, axis=0) + dy

    return lower, upper


def plot_result(result, reference=None, filename=None):

    import matplotlib.pylab as pylab

    params = {
            # 'legend.fontsize': 'medium',
            #'figure.figsize': (10, 8),
            'legend.fontsize': 'small',
            'axes.labelsize': 'small',
            #   'axes.titlesize': 'medium',
            'xtick.labelsize': 'small',
            'ytick.labelsize': 'small'
    }

    pylab.rcParams.update(params)

    time = result['time']
    names = result.dtype.names[1:]

    if len(names) > 0:

        fig, axes = plt.subplots(len(names), sharex=True)

        fig.set_facecolor('white')

        if not isinstance(axes, Iterable):
            axes = [axes]

        for ax, name in zip(axes, names):

            ax.grid(b=True, which='both', color='0.8', linestyle='-', zorder=0)

            if reference is not None and name in reference.dtype.names:
                t_ref = reference['time']
                y_ref = reference[name]
                lower, upper = get_limits(y_ref)
                ax.fill_between(t_ref, lower, upper, color=(1, 0.5, 0.5))

            ax.plot(time, result[name], 'b', label='result', zorder=101)

            ax.set_ylabel(name)

            ax.margins(x=0, y=0.1)

        if reference is not None:
            #ax.legend()
            plt.legend(bbox_to_anchor=(0, -0.4, 1., 0.1), loc=8, ncol=2, mode="normal", borderaxespad=0.5)


        fig.set_size_inches(w=12, h=8, forward=True)
        plt.tight_layout()
        fig.subplots_adjust(bottom=0.08)

        if filename is None:
            plt.show()
        else:
            dir, file = os.path.split(filename)
            if not os.path.isdir(dir):
                os.makedirs(dir)
            fig.savefig(filename=filename)


class TestSimulateFMU(TestCase):

    def __init__(self, *args, **kwargs):

        super(TestSimulateFMU, self).__init__(*args, **kwargs)

        self.testFMUsDirectory = r'Z:\Development\FMI\branches\public\Test_FMUs'
        self.tools = ['DS_FMU_Export_from_Simulink']

    @classmethod
    def setUpClass(cls):
        cls.html = open(os.path.join(reportDir, 'report.html'), 'w')
        cls.html.write('<html><body><table>')
        cls.html.write('<tr><th>Model</th><th>Outliers</th></tr>\n')

    @classmethod
    def tearDownClass(cls):
        cls.html.write('</table></body></html>')


def test_generator(baseDir, modelPath):
    def test(self):
        outliers = simulateFMU(os.path.join(baseDir, modelPath), reportDir=os.path.join(reportDir, modelPath))
        self.html.write('<tr><td><a href="' + os.path.join(modelPath, 'result.png') + '">' + modelPath + '</a></td><td>' + str(outliers) + '</td></tr>\n')
        self.assertTrue(outliers < 10, "Too many outliers: " + str(outliers))
    return test


fmiVersions = ['fmi1', 'fmi2']
fmiTypes = ['me', 'cs']
testFMUsDirectory = r'Z:\Development\FMI\branches\public\Test_FMUs'
tools = ['Dymola']
# tools = ['DS_FMU_Export_from_Simulink']
# tools = ['FMIToolbox_MATLAB']
# tools = ['MapleSim']
# tools = ['SimulationX']
# tools = ['OpenModelica']
# models = ['fullRobot']
models = ['BooleanNetwork1']
# models = ['ControlledTemperature']
# models = None
reportDir = r'Z:\Development\FMPy\CrossCheck'

for fmiVersion in fmiVersions:

    for fmiType in fmiTypes:

        platformDir = os.path.join(testFMUsDirectory,
                                   'FMI_1.0' if fmiVersion == 'fmi1' else 'FMI_2.0',
                                   'ModelExchange' if fmiType == 'me' else 'CoSimulation',
                                   fmpy.platform)

        for tool in os.listdir(platformDir):

            if tools is not None and not tool in tools:
                continue

            toolDir = os.path.join(platformDir, tool)
            versions = os.listdir(toolDir)
            version = sorted(versions)[-1]
            versionDir = os.path.join(toolDir, version)

            for model in os.listdir(versionDir):

                if models is not None and model not in models:
                    continue

                modelDir = os.path.join(versionDir, model)

                if not os.path.isdir(modelDir):
                    continue

                test = test_generator(testFMUsDirectory, os.path.join('FMI_1.0' if fmiVersion == 'fmi1' else 'FMI_2.0',
                                   'ModelExchange' if fmiType == 'me' else 'CoSimulation',
                                   fmpy.platform, tool, version, model))

                setattr(TestSimulateFMU, 'test_' + fmiVersion + '_' + fmiType + '_' + tool +'_' + model, test)


if __name__ == '__main__':

    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\FMUSDK\2.0.4'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\CoSimulation\win64\FMIToolbox_MATLAB\2.3'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\Dymola\2017'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\MapleSim\2016.2'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\SimulationX\3.7.41138'
    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.3.0'

    #test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_2.0\CoSimulation\win64\AMESim\15'

    test_fmu_dir = r'Z:\Development\FMI\branches\public\Test_FMUs'

    fmu_paths = [

        # Windows 64-bit

        # FMI 1.0

        # Co-Simulation

        r'FMI_1.0\CoSimulation\win64\AMESim\14\fuelrail_cs',
        r'FMI_1.0\CoSimulation\win64\AMESim\14\MIS_cs',
        r'FMI_1.0\CoSimulation\win64\AMESim\14\steam_plant',

        r'FMI_1.0\CoSimulation\win64\AVL_Cruise\v2014\Battery',
        r'FMI_1.0\CoSimulation\win64\AVL_Cruise\v2014\DMF', # some signals different
        # r'FMI_1.0\CoSimulation\win64\AVL_Cruise\v2014\EngineTestBed',
        r'FMI_1.0\CoSimulation\win64\AVL_Cruise\v2014\Man4WD', # different sample times?

        # line endings of the CSVs inconsistent:
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\BooleanNetwork1',
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\ControlledTemperature',
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\CoupledClutches',
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\DFFREG',
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\MixtureGases',
        #           r'FMI_1.0\CoSimulation\win64\CATIA\R2015x\Rectifier',

        r'FMI_1.0\CoSimulation\win64\MapleSim\2016.1\ControlledTemperature',
        r'FMI_1.0\CoSimulation\win64\MapleSim\2016.1\CoupledClutches',
        r'FMI_1.0\CoSimulation\win64\MapleSim\2016.1\Rectifier',

        r'FMI_1.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\BouncingBalls_sf',
        r'FMI_1.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel1_sf',
        r'FMI_1.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel2_sf',
        r'FMI_1.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TriggeredSubsystems_sf',

        r'FMI_1.0\CoSimulation\win64\Dymola\2017\BooleanNetwork1',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\ControlledTemperature',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\CoupledClutches',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\DFFREG',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\Engine1b',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\fullRobot',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\IntegerNetwork1',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\MixtureGases',
        r'FMI_1.0\CoSimulation\win64\Dymola\2017\Rectifier',

        r'FMI_1.0\CoSimulation\win64\SimulationX\3.6\ControlledTemperature',
        r'FMI_1.0\CoSimulation\win64\SimulationX\3.6\CoupledClutches',
        r'FMI_1.0\CoSimulation\win64\SimulationX\3.6\DFFREG',
        r'FMI_1.0\CoSimulation\win64\SimulationX\3.6\Engine1b',
        r'FMI_1.0\CoSimulation\win64\SimulationX\3.6\Rectifier',

        # model exchange
        r'FMI_1.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\BouncingBalls_sf',
        r'FMI_1.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel1_sf',
        r'FMI_1.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel2_sf',
        r'FMI_1.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TriggeredSubsystems_sf',

        r'FMI_1.0\ModelExchange\win64\Dymola\2017\BooleanNetwork1',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\ControlledTemperature',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\CoupledClutches',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\DFFREG',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\Engine1b',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\fullRobot',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\IntegerNetwork1',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\MixtureGases',
        r'FMI_1.0\ModelExchange\win64\Dymola\2017\Rectifier',

        r'FMI_1.0\ModelExchange\win64\MapleSim\2016.1\ControlledTemperature',
        r'FMI_1.0\ModelExchange\win64\MapleSim\2016.1\CoupledClutches',
        r'FMI_1.0\ModelExchange\win64\MapleSim\2016.1\Rectifier',

        r'FMI_1.0\ModelExchange\win64\SimulationX\3.6\ControlledTemperature',
        r'FMI_1.0\ModelExchange\win64\SimulationX\3.6\CoupledClutches',
        r'FMI_1.0\ModelExchange\win64\SimulationX\3.6\DFFREG',
        r'FMI_1.0\ModelExchange\win64\SimulationX\3.6\Engine1b',
        r'FMI_1.0\ModelExchange\win64\SimulationX\3.6\Rectifier',

        # FMI 2.0

        # co-simulation

        r'FMI_2.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\BouncingBalls_sf',
        r'FMI_2.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel1_sf',
        r'FMI_2.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel2_sf',
        r'FMI_2.0\CoSimulation\win64\DS_FMU_Export_from_Simulink\2.2.0\TriggeredSubsystems_sf',

        r'FMI_2.0\CoSimulation\win64\Dymola\2017\BooleanNetwork1',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\ControlledTemperature',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\CoupledClutches',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\DFFREG',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\IntegerNetwork1',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\MixtureGases',
        r'FMI_2.0\CoSimulation\win64\Dymola\2017\Rectifier',

        r'FMI_2.0\CoSimulation\win64\MapleSim\2016.1\ControlledTemperature',
        r'FMI_2.0\CoSimulation\win64\MapleSim\2016.1\CoupledClutches',
        r'FMI_2.0\CoSimulation\win64\MapleSim\2016.1\Rectifier',

        # model exchange

        r'FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\BouncingBalls_sf',
        r'FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel1_sf',
        r'FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TestModel2_sf',
        r'FMI_2.0\ModelExchange\win64\DS_FMU_Export_from_Simulink\2.2.0\TriggeredSubsystems_sf',

        r'FMI_2.0\ModelExchange\win64\Dymola\2017\BooleanNetwork1',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\ControlledTemperature',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\CoupledClutches',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\DFFREG',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\IntegerNetwork1',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\MixtureGases',
        r'FMI_2.0\ModelExchange\win64\Dymola\2017\Rectifier',

        r'FMI_2.0\ModelExchange\win64\MapleSim\2016.1\ControlledTemperature',
        r'FMI_2.0\ModelExchange\win64\MapleSim\2016.1\CoupledClutches',
        r'FMI_2.0\ModelExchange\win64\MapleSim\2016.1\Rectifier',
    ]


    with open('report.html', 'w') as html:

        html.write('<html><body><table>')

        for path in fmu_paths:

            subdir = os.path.join(test_fmu_dir, path)

            subdi2 = r'Z:\Development\FMI\branches\public\Test_FMUs\FMI_1.0\CoSimulation\win64\MapleSim\2016.1\ControlledTemperature'

            args = {'path': subdir}

            for file in os.listdir(subdir):

                if file.endswith('.fmu'):
                    args['fmu_filename'] = file

                if file.endswith('_in.csv'):
                    args['input_filename'] = file

                if file.endswith('_cc.csv'):
                    args['reference_filename'] = file

                if file.endswith('_cc.bat'):
                    args['batch_filename'] = file

            if 'fmu_filename' in args:
                dev = simulateFMU(**args)
                html.write('<tr><td>' + path + '</td><td>' + '%.2f' % (dev * 100) + ' %</td></tr>\n')

        html.write('</table></body></html>')
