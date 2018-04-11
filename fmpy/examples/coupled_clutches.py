from __future__ import print_function
from fmpy import simulate_fmu
from fmpy.util import download_test_file
import numpy as np


def simulate_coupled_clutches(fmi_version='2.0',
                              fmi_type='ModelExchange',
                              output=['outputs[1]', 'outputs[2]', 'outputs[3]', 'outputs[4]'],
                              solver='CVode',
                              events=True,
                              fmi_logging=False,
                              show_plot=True):

    # download the FMU and input file
    for filename in ['CoupledClutches.fmu', 'CoupledClutches_in.csv']:
        download_test_file(fmi_version, fmi_type, 'MapleSim', '2016.2', 'CoupledClutches', filename)

    print("Loading input...")
    input = np.genfromtxt('CoupledClutches_in.csv', delimiter=',', names=True)

    print("Simulating CoupledClutches.fmu (FMI %s, %s, %s)..." % (fmi_version, fmi_type, solver))
    result = simulate_fmu(
        filename='CoupledClutches.fmu',
        validate=False,
        start_time=0,
        stop_time=1.5,
        solver=solver,
        step_size=1e-2,
        output_interval=2e-2,
        record_events=events,
        start_values={'CoupledClutches1_freqHz': 0.4},
        input=input,
        output=output,
        fmi_call_logger=lambda s: print('[FMI] ' + s) if fmi_logging else None)

    if show_plot:
        print("Plotting results...")
        from fmpy.util import plot_result
        plot_result(result=result,
                    window_title="CoupledClutches.fmu (FMI %s, %s, %s)" % (fmi_version, fmi_type, solver),
                    events=events)

    print("Done.")

    return result


if __name__ == '__main__':

    simulate_coupled_clutches()
